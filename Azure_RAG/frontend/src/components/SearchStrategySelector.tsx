import React from 'react';
import { SearchStrategy } from '../types';

interface SearchStrategySelectorProps {
  selected: SearchStrategy;
  onChange: (strategy: SearchStrategy) => void;
}

const strategies: Array<{
  value: SearchStrategy;
  label: string;
  description: string;
}> = [
  {
    value: SearchStrategy.HYBRID,
    label: 'Hybrid',
    description: 'Best overall: Combines keyword + semantic search (Recommended)',
  },
  {
    value: SearchStrategy.SEMANTIC,
    label: 'Semantic',
    description: 'Find similar concepts and meanings using AI',
  },
  {
    value: SearchStrategy.BM25,
    label: 'Keyword',
    description: 'Traditional exact term matching (BM25)',
  },
  {
    value: SearchStrategy.ENTITY,
    label: 'Entity',
    description: 'Search by people, organizations, topics, etc.',
  },
  {
    value: SearchStrategy.ADVANCED,
    label: 'Advanced',
    description: 'All methods combined with entity boosting',
  },
];

export const SearchStrategySelector: React.FC<SearchStrategySelectorProps> = ({
  selected,
  onChange,
}) => {
  return (
    <div className="w-full">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Search Strategy
      </label>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {strategies.map((strategy) => (
          <button
            key={strategy.value}
            onClick={() => onChange(strategy.value)}
            className={`
              relative p-4 rounded-lg border-2 text-left transition-all
              ${
                selected === strategy.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
              }
            `}
          >
            <div className="flex items-start justify-between">
              <h3 className="font-semibold text-gray-900 text-sm">{strategy.label}</h3>
              {selected === strategy.value && (
                <svg
                  className="w-5 h-5 text-blue-500"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </div>
            <p className="mt-1 text-xs text-gray-500">{strategy.description}</p>
          </button>
        ))}
      </div>
    </div>
  );
};
