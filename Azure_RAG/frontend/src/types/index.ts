// API Types matching the backend models

export enum SearchStrategy {
  BM25 = "bm25",
  SEMANTIC = "semantic",
  ENTITY = "entity",
  HYBRID = "hybrid",
  ADVANCED = "advanced",
}

export enum IndexingStatus {
  PENDING = "pending",
  PROCESSING = "processing",
  EXTRACTING_ENTITIES = "extracting_entities",
  EMBEDDING = "embedding",
  INDEXING = "indexing",
  COMPLETED = "completed",
  FAILED = "failed",
}

export interface EntityFilters {
  people?: string[];
  organizations?: string[];
  locations?: string[];
  dates?: string[];
  topics?: string[];
  technical_terms?: string[];
}

export interface ExtractedEntities {
  people: string[];
  organizations: string[];
  locations: string[];
  dates: string[];
  topics: string[];
  technical_terms: string[];
}

export interface UploadResponse {
  document_id: string;
  filename: string;
  size_bytes: number;
  blob_url: string;
  message: string;
}

export interface IndexingProgress {
  document_id: string;
  status: IndexingStatus;
  progress_percentage: number;
  current_step: string;
  total_chunks?: number;
  processed_chunks?: number;
  entities_extracted?: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
}

export interface SearchRequest {
  query: string;
  strategy?: SearchStrategy;
  entity_filters?: EntityFilters;
  top_k?: number;
  include_entities?: boolean;
}

export interface SearchResult {
  chunk_id: string;
  content: string;
  score: number;
  metadata: {
    document_id: string;
    filename: string;
    chunk_index: number;
    page_numbers?: number[];
  };
  entities?: Record<string, string[]>;
  match_explanation?: string;
}

export interface SearchResponse {
  query: string;
  strategy: SearchStrategy;
  results: SearchResult[];
  total_found: number;
  cache_hit: boolean;
}

export interface QueryRequest {
  query: string;
  document_ids?: string[];
  stream?: boolean;
}

export interface QueryResponse {
  query: string;
  answer: string;
  sources: Array<{
    index: number;
    content: string;
    metadata: Record<string, any>;
    score: number;
    entities?: Record<string, string[]>;
  }>;
  confidence?: number;
  cache_hit: boolean;
}

export interface HealthResponse {
  status: string;
  version: string;
  services: Record<string, string>;
}
