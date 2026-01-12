import React, { useState } from 'react';
import { apiClient } from '../services/api';
import type { QueryResponse } from '../types';
import { SearchStrategy } from '../types';

interface ChatInterfaceProps {
  strategy: SearchStrategy;
  onResponse: (response: QueryResponse) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ strategy, onResponse }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.ragQuery({ query: query.trim() });
      onResponse(response);
      setQuery(''); // Clear input after successful query
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Query failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
            Ask a Question
          </label>
          <div className="relative">
            <input
              id="query"
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., What are the main findings in the document?"
              className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className={`
                absolute right-2 top-1/2 -translate-y-1/2
                p-2 rounded-md transition-colors
                ${
                  loading || !query.trim()
                    ? 'text-gray-400 cursor-not-allowed'
                    : 'text-blue-600 hover:bg-blue-50'
                }
              `}
            >
              {loading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
              ) : (
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M14 5l7 7m0 0l-7 7m7-7H3"
                  />
                </svg>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <div className="flex items-center text-xs text-gray-500">
          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
          Using {strategy.toUpperCase()} search strategy
        </div>
      </form>
    </div>
  );
};
