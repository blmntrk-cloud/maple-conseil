"""
Arme Fatale — Générateur de présentations clients SCHMIDT
Backend Flask — API REST pour le parsing XML et la génération PPTX
"""

import os
import tempfile
import json
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from xml_parser import InSituXMLParser
from pptx_generator import PPTXGenerator
from catalog import CatalogManager
from image_handler import ImageHandler

app = Flask(__name__)
CORS(app)

# Initialisation des composants
catalog_manager = CatalogManager()
image_handler = ImageHandler()
pptx_generator = PPTXGenerator(catalog_manager, image_handler)

# Dossier temporaire pour les uploads
UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'arme-fatale-uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'service': 'Arme Fatale'})


@app.route('/api/parse-xml', methods=['POST'])
def parse_xml():
    """
    Parse an In Situ XML file and return structured project data.
    Expects multipart/form-data with 'xml_file' field.
    """
    if 'xml_file' not in request.files:
        return jsonify({'error': 'No XML file provided'}), 400

    file = request.files['xml_file']
    if not file.filename.endswith('.xml'):
        return jsonify({'error': 'File must be XML format'}), 400

    # Save temporarily
    xml_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(xml_path)

    try:
        parser = InSituXMLParser()
        project_data = parser.parse(xml_path)
        return jsonify({
            'success': True,
            'project': project_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(xml_path):
            os.remove(xml_path)


@app.route('/api/generate-pptx', methods=['POST'])
def generate_pptx():
    """
    Generate a PPTX presentation from project data and images.
    Expects JSON body with:
    - project: parsed project data (from /api/parse-xml)
    - images: list of image file paths (server-side) or base64-encoded images
    - options: generation options (template name, color scheme, etc.)
    """
    data = request.get_json()
    if not data or 'project' not in data:
        return jsonify({'error': 'No project data provided'}), 400

    project = data['project']
    images = data.get('images', [])
    options = data.get('options', {})

    try:
        output_path = pptx_generator.generate(project, images, options)
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"Presentation_{project.get('client_name', 'client')}.pptx",
            mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/upload-images', methods=['POST'])
def upload_images():
    """
    Upload multiple images (3D renders, linéaires).
    Returns list of server-side file paths.
    """
    if 'images' not in request.files:
        return jsonify({'error': 'No images provided'}), 400

    files = request.files.getlist('images')
    saved_paths = []

    for file in files:
        if file.filename == '':
            continue
        # Validate image format
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_extensions:
            continue

        # Save to temp folder
        filename = f"img_{len(saved_paths)}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        saved_paths.append({
            'path': filepath,
            'name': file.filename,
            'type': image_handler.classify_image(filepath)
        })

    return jsonify({
        'success': True,
        'images': saved_paths
    })


@app.route('/api/catalog/bsh', methods=['GET'])
def get_bsh_catalog():
    """Return BSH appliance catalog."""
    return jsonify(catalog_manager.get_bsh_catalog())


@app.route('/api/catalog/franke', methods=['GET'])
def get_franke_catalog():
    """Return Franke sink/faucet catalog."""
    return jsonify(catalog_manager.get_franke_catalog())


@app.route('/api/catalog/search', methods=['GET'])
def search_catalog():
    """Search across all catalogs by reference code."""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'No search query provided'}), 400

    results = catalog_manager.search(query)
    return jsonify({'results': results})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
