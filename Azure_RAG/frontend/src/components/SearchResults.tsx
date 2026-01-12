import React from 'react';
import type { QueryResponse } from '../types';

interface SearchResultsProps {
  response: QueryResponse | null;
}

export const SearchResults: React.FC<SearchResultsProps> = ({ response }) => {
  if (!response) {
    return (
      <div className="w-full p-12 text-center text-gray-500">
        <svg
          className="mx-auto h-12 w-12 text-gray-400 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
          />
        </svg>
        <p>Ask a question to see results</p>
      </div>
    );
  }

  return (
    <div className="w-full space-y-6">
      {/* Query */}
      <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
        <div className="flex items-start">
          <svg
            className="w-5 h-5 text-gray-500 mt-0.5 mr-2 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div className="flex-1">
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Question</p>
            <p className="text-gray-900">{response.query}</p>
          </div>
        </div>
      </div>

      {/* Answer */}
      <div className="p-6 bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <svg
              className="w-5 h-5 text-blue-500 mr-2"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
            <h3 className="text-lg font-semibold text-gray-900">Answer</h3>
          </div>

          {response.cache_hit && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              Cached
            </span>
          )}
        </div>

        <div className="prose prose-sm max-w-none">
          <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">{response.answer}</p>
        </div>

        {response.confidence !== undefined && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Confidence</span>
              <div className="flex items-center">
                <div className="w-32 bg-gray-200 rounded-full h-2 mr-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full"
                    style={{ width: `${(response.confidence || 0) * 100}%` }}
                  ></div>
                </div>
                <span className="font-medium text-gray-900">
                  {Math.round((response.confidence || 0) * 100)}%
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Sources */}
      {response.sources.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            Sources ({response.sources.length})
          </h3>

          <div className="space-y-3">
            {response.sources.map((source) => (
              <div
                key={source.index}
                className="p-4 bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center flex-wrap gap-2">
                    <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-600 text-xs font-semibold">
                      {source.index}
                    </span>
                    <span className="text-sm font-medium text-gray-900">
                      {source.metadata.filename || 'Unknown'}
                    </span>
                    {source.metadata.page_numbers && source.metadata.page_numbers.length > 0 && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-purple-100 text-purple-700 text-xs font-medium">
                        Page {source.metadata.page_numbers.length === 1
                          ? source.metadata.page_numbers[0]
                          : `${source.metadata.page_numbers[0]}-${source.metadata.page_numbers[source.metadata.page_numbers.length - 1]}`}
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-gray-500">
                    Score: {source.score.toFixed(2)}
                  </span>
                </div>

                <p className="text-sm text-gray-600 line-clamp-3">{source.content}</p>

                {source.entities && Object.keys(source.entities).length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1">
                    {Object.entries(source.entities).map(
                      ([type, values]) =>
                        values.length > 0 && (
                          <div key={type} className="inline-flex items-center">
                            {values.slice(0, 3).map((value, idx) => (
                              <span
                                key={idx}
                                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700 mr-1"
                              >
                                {value}
                              </span>
                            ))}
                          </div>
                        )
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
