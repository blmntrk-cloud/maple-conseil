import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, Image as ImageIcon, FileCheck, Loader2, Download, AlertCircle } from 'lucide-react';
import { parseXML, uploadImages, generatePPTX, ProjectData, ImageInfo } from './api/client';

type Step = 'upload' | 'preview' | 'generating' | 'done';

function App() {
  const [step, setStep] = useState<Step>('upload');
  const [xmlFile, setXmlFile] = useState<File | null>(null);
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const [project, setProject] = useState<ProjectData | null>(null);
  const [images, setImages] = useState<ImageInfo[]>([]);
  const [error, setError] = useState<string>('');
  const [pptxUrl, setPptxUrl] = useState<string>('');

  const onXMLDrop = useCallback((accepted: File[]) => {
    if (accepted.length > 0) {
      setXmlFile(accepted[0]);
      setError('');
    }
  }, []);

  const onImageDrop = useCallback((accepted: File[]) => {
    setImageFiles((prev) => [...prev, ...accepted]);
    setError('');
  }, []);

  const xmlDropzone = useDropzone({
    onDrop: onXMLDrop,
    accept: { 'text/xml': ['.xml'] },
    multiple: false,
  });

  const imageDropzone = useDropzone({
    onDrop: onImageDrop,
    accept: {
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/webp': ['.webp'],
    },
    multiple: true,
  });

  const handleParseAndUpload = async () => {
    if (!xmlFile) {
      setError('Veuillez sélectionner un fichier XML');
      return;
    }
    setError('');
    setStep('preview');
    try {
      const parsed = await parseXML(xmlFile);
      setProject(parsed);
      if (imageFiles.length > 0) {
        const uploaded = await uploadImages(imageFiles);
        setImages(uploaded);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors du parsing XML');
      setStep('upload');
    }
  };

  const handleGenerate = async () => {
    if (!project) return;
    setStep('generating');
    setError('');
    try {
      const blob = await generatePPTX(project, images);
      const url = URL.createObjectURL(blob);
      setPptxUrl(url);
      setStep('done');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la génération PPTX');
      setStep('preview');
    }
  };

  const handleReset = () => {
    setStep('upload');
    setXmlFile(null);
    setImageFiles([]);
    setProject(null);
    setImages([]);
    setError('');
    setPptxUrl('');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-[#333333] text-white px-8 py-4 flex items-center gap-4">
        <div className="w-1 h-8 bg-[#E86A1E] rounded" />
        <div>
          <h1 className="text-xl font-bold">Arme Fatale</h1>
          <p className="text-sm text-gray-400">Générateur de présentations clients SCHMIDT</p>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-8">
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3 text-red-700">
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        {/* Step indicator */}
        <div className="flex items-center gap-2 mb-8">
          {['Importer', 'Aperçu', 'Générer', 'Télécharger'].map((label, i) => {
            const stepOrder = ['upload', 'preview', 'generating', 'done'];
            const isActive = stepOrder.indexOf(step) >= i;
            return (
              <div key={label} className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                  isActive ? 'bg-[#E86A1E] text-white' : 'bg-gray-200 text-gray-500'
                }`}>
                  {i + 1}
                </div>
                <span className={`ml-2 text-sm ${isActive ? 'text-[#333333] font-medium' : 'text-gray-400'}`}>
                  {label}
                </span>
                {i < 3 && <div className={`w-12 h-0.5 mx-3 ${isActive ? 'bg-[#E86A1E]' : 'bg-gray-200'}`} />}
              </div>
            );
          })}
        </div>

        {/* Step: Upload */}
        {step === 'upload' && (
          <div className="space-y-6">
            {/* XML Upload */}
            <div
              {...xmlDropzone.getRootProps()}
              className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
                xmlDropzone.isDragActive ? 'border-[#E86A1E] bg-orange-50' : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input {...xmlDropzone.getInputProps()} />
              {xmlFile ? (
                <div className="flex flex-col items-center gap-2">
                  <FileCheck size={48} className="text-green-500" />
                  <p className="text-lg font-medium text-gray-700">{xmlFile.name}</p>
                  <p className="text-sm text-gray-500">Cliquez pour changer</p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <FileText size={48} className="text-gray-400" />
                  <p className="text-lg font-medium text-gray-700">
                    Déposez votre fichier XML In Situ ici
                  </p>
                  <p className="text-sm text-gray-500">ou cliquez pour parcourir</p>
                </div>
              )}
            </div>

            {/* Image Upload */}
            <div
              {...imageDropzone.getRootProps()}
              className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
                imageDropzone.isDragActive ? 'border-[#E86A1E] bg-orange-50' : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input {...imageDropzone.getInputProps()} />
              <div className="flex flex-col items-center gap-2">
                <ImageIcon size={48} className="text-gray-400" />
                <p className="text-lg font-medium text-gray-700">
                  Déposez vos visuels (renders 3D, linéaires) ici
                </p>
                <p className="text-sm text-gray-500">JPG, PNG, WEBP — ou cliquez pour parcourir</p>
                {imageFiles.length > 0 && (
                  <p className="text-sm text-[#E86A1E] font-medium mt-2">
                    {imageFiles.length} image(s) sélectionnée(s)
                  </p>
                )}
              </div>
            </div>

            <button
              onClick={handleParseAndUpload}
              disabled={!xmlFile}
              className="w-full bg-[#E86A1E] text-white py-4 rounded-xl font-bold text-lg hover:bg-[#d45f1a] transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              Analyser le projet
            </button>
          </div>
        )}

        {/* Step: Preview */}
        {step === 'preview' && project && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-xl font-bold text-[#333333] mb-4">Aperçu du projet</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Client</p>
                  <p className="font-medium">{project.client.name || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Référence</p>
                  <p className="font-medium">{project.project_info.reference || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Date</p>
                  <p className="font-medium">{project.project_info.date || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Commercial</p>
                  <p className="font-medium">{project.project_info.commercial || 'N/A'}</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-4 gap-4">
              {[
                { label: 'Pièces', count: project.rooms.length },
                { label: 'Meubles', count: project.cabinets.length },
                { label: 'Finitions', count: project.finishes.length },
                { label: 'Électroménager', count: project.appliances.length },
              ].map((stat) => (
                <div key={stat.label} className="bg-white rounded-xl shadow-sm p-4 text-center">
                  <p className="text-3xl font-bold text-[#E86A1E]">{stat.count}</p>
                  <p className="text-sm text-gray-500">{stat.label}</p>
                </div>
              ))}
            </div>

            {project.cabinets.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm p-6">
                <h3 className="font-bold text-[#333333] mb-3">Meubles</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2">Référence</th>
                        <th className="text-left py-2">Type</th>
                        <th className="text-left py-2">Largeur</th>
                        <th className="text-left py-2">Qté</th>
                      </tr>
                    </thead>
                    <tbody>
                      {project.cabinets.slice(0, 10).map((c, i) => (
                        <tr key={i} className="border-b">
                          <td className="py-2 font-mono">{c.reference}</td>
                          <td className="py-2">{c.type}</td>
                          <td className="py-2">{c.width}</td>
                          <td className="py-2">{c.quantity}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {images.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm p-6">
                <h3 className="font-bold text-[#333333] mb-3">Images ({images.length})</h3>
                <div className="grid grid-cols-4 gap-3">
                  {images.map((img, i) => (
                    <div key={i} className="bg-gray-100 rounded-lg p-3 text-center">
                      <p className="text-sm font-medium truncate">{img.name}</p>
                      <p className="text-xs text-gray-500">{img.type}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-4">
              <button
                onClick={handleReset}
                className="px-6 py-3 rounded-xl border border-gray-300 text-gray-700 font-medium hover:bg-gray-50"
              >
                Recommencer
              </button>
              <button
                onClick={handleGenerate}
                className="flex-1 bg-[#E86A1E] text-white py-3 rounded-xl font-bold text-lg hover:bg-[#d45f1a] transition-colors"
              >
                Générer la présentation
              </button>
            </div>
          </div>
        )}

        {/* Step: Generating */}
        {step === 'generating' && (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 size={64} className="text-[#E86A1E] animate-spin" />
            <p className="mt-4 text-lg text-gray-600">Génération de la présentation en cours...</p>
          </div>
        )}

        {/* Step: Done */}
        {step === 'done' && (
          <div className="flex flex-col items-center justify-center py-20">
            <FileCheck size={64} className="text-green-500" />
            <p className="mt-4 text-xl font-bold text-[#333333]">Présentation générée !</p>
            <p className="mt-2 text-gray-600">Votre fichier PPTX est prêt à télécharger.</p>
            <a
              href={pptxUrl}
              download={`Presentation_${project?.client.name || 'client'}.pptx`}
              className="mt-6 flex items-center gap-2 bg-[#E86A1E] text-white px-8 py-3 rounded-xl font-bold hover:bg-[#d45f1a] transition-colors"
            >
              <Download size={20} />
              Télécharger le PPTX
            </a>
            <button
              onClick={handleReset}
              className="mt-4 text-gray-500 hover:text-gray-700"
            >
              Générer une autre présentation
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
