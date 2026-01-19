/**
 * Alert card component for fraud alert queue
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';

export interface Alert {
  id: string;
  transaction_id: string;
  user_id: string;
  amount: number;
  merchant_name: string;
  fraud_score: number;
  triggered_rules: string[];
  explanation?: string;
  status: 'new' | 'investigating' | 'resolved' | 'false_positive';
  priority: 'critical' | 'high' | 'medium' | 'low';
  assigned_to?: string;
  created_at: string;
  updated_at?: string;
}

export interface AlertCardProps {
  alert: Alert;
  onStatusChange?: (alertId: string, newStatus: Alert['status']) => void;
  onAssign?: (alertId: string, assignee: string) => void;
}

const getStatusStyles = (status: Alert['status']) => {
  switch (status) {
    case 'new':
      return 'bg-red-100 text-red-800 border-red-200';
    case 'investigating':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'resolved':
      return 'bg-green-100 text-green-800 border-green-200';
    case 'false_positive':
      return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

const getPriorityStyles = (priority: Alert['priority']) => {
  switch (priority) {
    case 'critical':
      return 'bg-red-600 text-white';
    case 'high':
      return 'bg-orange-600 text-white';
    case 'medium':
      return 'bg-yellow-600 text-white';
    case 'low':
      return 'bg-blue-600 text-white';
  }
};

export const AlertCard = ({ alert, onStatusChange, onAssign }: AlertCardProps) => {
  const navigate = useNavigate();
  const [showActions, setShowActions] = useState(false);

  const timeAgo = formatDistanceToNow(new Date(alert.created_at), { addSuffix: true });

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={`px-2 py-1 text-xs font-semibold rounded ${getPriorityStyles(alert.priority)}`}>
            {alert.priority.toUpperCase()}
          </span>
          <span className={`px-2 py-1 text-xs font-medium border rounded ${getStatusStyles(alert.status)}`}>
            {alert.status.replace('_', ' ').toUpperCase()}
          </span>
        </div>
        <button
          onClick={() => setShowActions(!showActions)}
          className="text-gray-400 hover:text-gray-600"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="space-y-2">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-mono text-gray-500">
              Alert #{alert.id.slice(0, 8)}...
            </p>
            <h3 className="text-lg font-semibold text-gray-900 mt-1">
              ${alert.amount.toFixed(2)} @ {alert.merchant_name}
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Fraud Score: <span className="font-bold text-red-600">{alert.fraud_score.toFixed(1)}</span>
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-500">{timeAgo}</p>
          </div>
        </div>

        {/* Triggered Rules */}
        {alert.triggered_rules.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {alert.triggered_rules.slice(0, 3).map((rule) => (
              <span key={rule} className="px-2 py-0.5 text-xs bg-red-100 text-red-700 rounded">
                {rule.replace(/_/g, ' ')}
              </span>
            ))}
            {alert.triggered_rules.length > 3 && (
              <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                +{alert.triggered_rules.length - 3} more
              </span>
            )}
          </div>
        )}

        {/* Explanation Preview */}
        {alert.explanation && (
          <p className="text-sm text-gray-600 line-clamp-2 mt-2">
            {alert.explanation}
          </p>
        )}

        {/* Assigned To */}
        {alert.assigned_to && (
          <p className="text-xs text-gray-500 mt-2">
            Assigned to: <span className="font-medium">{alert.assigned_to}</span>
          </p>
        )}
      </div>

      {/* Actions Menu */}
      {showActions && (
        <div className="mt-4 pt-4 border-t border-gray-200 space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => onStatusChange?.(alert.id, 'investigating')}
              className="px-3 py-2 text-sm font-medium text-yellow-700 bg-yellow-50 border border-yellow-200 rounded hover:bg-yellow-100"
            >
              Investigate
            </button>
            <button
              onClick={() => onStatusChange?.(alert.id, 'resolved')}
              className="px-3 py-2 text-sm font-medium text-green-700 bg-green-50 border border-green-200 rounded hover:bg-green-100"
            >
              Resolve
            </button>
            <button
              onClick={() => onStatusChange?.(alert.id, 'false_positive')}
              className="px-3 py-2 text-sm font-medium text-gray-700 bg-gray-50 border border-gray-200 rounded hover:bg-gray-100"
            >
              False Positive
            </button>
            <button
              onClick={() => navigate(`/transactions/${alert.transaction_id}`)}
              className="px-3 py-2 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded hover:bg-blue-100"
            >
              View Details
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
