import axios, { type AxiosInstance } from 'axios';
import type {
  UploadResponse,
  IndexingProgress,
  SearchRequest,
  SearchResponse,
  QueryRequest,
  QueryResponse,
  HealthResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api`,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // Upload PDF
  async uploadPDF(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post<UploadResponse>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  // Start indexing
  async startIndexing(
    documentId: string,
    extractEntities: boolean = true
  ): Promise<IndexingProgress> {
    const response = await this.client.post<IndexingProgress>(
      `/index/${documentId}`,
      {
        document_id: documentId,
        extract_entities: extractEntities,
      }
    );

    return response.data;
  }

  // Get indexing status
  async getIndexingStatus(documentId: string): Promise<IndexingProgress> {
    const response = await this.client.get<IndexingProgress>(`/index/${documentId}`);
    return response.data;
  }

  // Search documents
  async search(request: SearchRequest): Promise<SearchResponse> {
    const response = await this.client.post<SearchResponse>('/query/search', request);
    return response.data;
  }

  // RAG query
  async ragQuery(request: QueryRequest): Promise<QueryResponse> {
    const response = await this.client.post<QueryResponse>('/query/rag', request);
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<HealthResponse> {
    const response = await axios.get<HealthResponse>(`${API_BASE_URL}/health`);
    return response.data;
  }

  // Clear cache
  async clearCache(): Promise<{ message: string; cleared_keys: number }> {
    const response = await this.client.delete<{ message: string; cleared_keys: number }>(
      '/cache/clear'
    );
    return response.data;
  }
}

export const apiClient = new APIClient();
