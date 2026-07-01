import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
});

export interface ProjectData {
  source_file: string;
  client: {
    name: string;
    address: string;
    phone: string;
    email: string;
    reference: string;
  };
  project_info: {
    name: string;
    reference: string;
    date: string;
    store: string;
    commercial: string;
    version: string;
  };
  rooms: Array<{
    name: string;
    length: string;
    width: string;
    height: string;
    shape: string;
  }>;
  cabinets: Array<{
    reference: string;
    type: string;
    category: string;
    width: string;
    height: string;
    depth: string;
    quantity: string;
    description: string;
    finish_code: string;
    position: string;
  }>;
  finishes: Array<{
    code: string;
    name: string;
    category: string;
  }>;
  handles: Array<{
    code: string;
    name: string;
    quantity: string;
  }>;
  worktops: Array<{
    material: string;
    name: string;
    type: string;
    color: string;
    reference: string;
    length: string;
    width: string;
    thickness: string;
  }>;
  appliances: Array<{
    reference: string;
    type: string;
    brand: string;
    model: string;
    description: string;
  }>;
  sinks: Array<{
    reference: string;
    brand: string;
    model: string;
    material: string;
    bowls: string;
  }>;
  faucets: Array<{
    reference: string;
    brand: string;
    model: string;
    finish: string;
  }>;
}

export interface ImageInfo {
  path: string;
  name: string;
  type: string;
}

export const parseXML = async (file: File): Promise<ProjectData> => {
  const formData = new FormData();
  formData.append('xml_file', file);
  const response = await api.post('/parse-xml', formData);
  return response.data.project;
};

export const uploadImages = async (files: File[]): Promise<ImageInfo[]> => {
  const formData = new FormData();
  files.forEach((file) => formData.append('images', file));
  const response = await api.post('/upload-images', formData);
  return response.data.images;
};

export const generatePPTX = async (
  project: ProjectData,
  images: ImageInfo[],
  options: Record<string, unknown> = {}
): Promise<Blob> => {
  const response = await api.post(
    '/generate-pptx',
    { project, images, options },
    { responseType: 'blob' }
  );
  return response.data;
};

export const searchCatalog = async (query: string) => {
  const response = await api.get('/catalog/search', { params: { q: query } });
  return response.data.results;
};
