import React, { useEffect, useState } from 'react';
import { apiClient } from '../services/api';
import type { IndexingProgress } from '../types';
import { IndexingStatus as Status } from '../types';

interface IndexingStatusProps {
  documentId: string;
  onComplete: () => void;
}

export const IndexingStatusComponent: React.FC<IndexingStatusProps> = ({
  documentId,
  onComplete,
}) => {
  const [status, setStatus] = useState<IndexingProgress | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const pollStatus = async () => {
      try {
        const progress = await apiClient.getIndexingStatus(documentId);
        setStatus(progress);

        if (progress.status === Status.COMPLETED) {
          onComplete();
        } else if (progress.status === Status.FAILED) {
          setError(progress.error_message || 'Indexing failed');
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to get status');
      }
    };

    // Poll every 2 seconds
    const interval = setInterval(pollStatus, 2000);
    pollStatus(); // Initial call

    return () => clearInterval(interval);
  }, [documentId, onComplete]);

  if (error) {
    return (
      <div className="w-full max-w-2xl mx-auto p-6 bg-red-50 border border-red-200 rounded-lg">
        <h3 className="text-lg font-semibold text-red-800 mb-2">Indexing Failed</h3>
        <p className="text-sm text-red-600">{error}</p>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="w-full max-w-2xl mx-auto p-6 bg-white border border-gray-200 rounded-lg">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-2 bg-gray-200 rounded w-full"></div>
        </div>
      </div>
    );
  }

  const getStatusColor = () => {
    switch (status.status) {
      case Status.COMPLETED:
        return 'bg-green-500';
      case Status.FAILED:
        return 'bg-red-500';
      case Status.PROCESSING:
      case Status.EXTRACTING_ENTITIES:
      case Status.EMBEDDING:
      case Status.INDEXING:
        return 'bg-blue-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getStatusLabel = () => {
    switch (status.status) {
      case Status.PENDING:
        return 'Pending';
      case Status.PROCESSING:
        return 'Processing PDF';
      case Status.EXTRACTING_ENTITIES:
        return 'Extracting Entities';
      case Status.EMBEDDING:
        return 'Generating Embeddings';
      case Status.INDEXING:
        return 'Indexing';
      case Status.COMPLETED:
        return 'Completed';
      case Status.FAILED:
        return 'Failed';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Indexing Progress</h3>
        <span className="text-sm font-medium text-gray-600">{status.progress_percentage}%</span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-2.5 mb-4">
        <div
          className={`h-2.5 rounded-full transition-all duration-500 ${getStatusColor()}`}
          style={{ width: `${status.progress_percentage}%` }}
        ></div>
      </div>

      {/* Status Details */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Status:</span>
          <span className="font-medium text-gray-800">{getStatusLabel()}</span>
        </div>

        <div className="text-sm text-gray-600">{status.current_step}</div>

        {status.total_chunks && (
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Chunks:</span>
            <span className="font-medium text-gray-800">
              {status.processed_chunks || 0} / {status.total_chunks}
            </span>
          </div>
        )}

        {status.entities_extracted !== undefined && (
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Entities Extracted:</span>
            <span className="font-medium text-gray-800">{status.entities_extracted}</span>
          </div>
        )}
      </div>

      {/* Loading Spinner */}
      {status.status !== Status.COMPLETED && status.status !== Status.FAILED && (
        <div className="mt-4 flex items-center justify-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
        </div>
      )}
    </div>
  );
};
