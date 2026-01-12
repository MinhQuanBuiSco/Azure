import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { apiClient } from '../services/api';
import type { UploadResponse } from '../types';

interface PDFUploaderProps {
  onUploadSuccess: (response: UploadResponse) => void;
}

export const PDFUploader: React.FC<PDFUploaderProps> = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;

      const file = acceptedFiles[0];
      setUploading(true);
      setError(null);

      try {
        const response = await apiClient.uploadPDF(file);
        onUploadSuccess(response);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Upload failed');
      } finally {
        setUploading(false);
      }
    },
    [onUploadSuccess]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024, // 50MB
  });

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
          transition-colors duration-200
          ${
            isDragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          }
          ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} disabled={uploading} />

        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          stroke="currentColor"
          fill="none"
          viewBox="0 0 48 48"
        >
          <path
            d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>

        <div className="mt-4">
          {uploading ? (
            <p className="text-blue-600 font-medium">Uploading...</p>
          ) : isDragActive ? (
            <p className="text-blue-600 font-medium">Drop the PDF here</p>
          ) : (
            <>
              <p className="text-gray-700 font-medium">
                Drag & drop a PDF file here, or click to select
              </p>
              <p className="text-sm text-gray-500 mt-1">
                Maximum file size: 50MB
              </p>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}
    </div>
  );
};
