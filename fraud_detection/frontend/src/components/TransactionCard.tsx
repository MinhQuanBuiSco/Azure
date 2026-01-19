/**
 * Transaction card component for real-time transaction feed
 */
import { formatDistanceToNow } from 'date-fns';

export interface Transaction {
  transaction_id: string;
  user_id: string;
  amount: number;
  merchant_name: string;
  fraud_score: number;
  risk_level: 'low' | 'medium' | 'high';
  is_fraud: boolean;
  is_blocked: boolean;
  processing_time_ms?: number;
  timestamp?: string;
}

export interface TransactionCardProps {
  transaction: Transaction;
  onClick?: () => void;
}

const getRiskBadgeStyles = (riskLevel: string) => {
  switch (riskLevel) {
    case 'high':
      return 'bg-red-100 text-red-800 border-red-200';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'low':
      return 'bg-green-100 text-green-800 border-green-200';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

const getScoreColor = (score: number) => {
  if (score >= 70) return 'text-red-600';
  if (score >= 30) return 'text-yellow-600';
  return 'text-green-600';
};

export const TransactionCard = ({ transaction, onClick }: TransactionCardProps) => {
  const riskBadgeStyles = getRiskBadgeStyles(transaction.risk_level);
  const scoreColor = getScoreColor(transaction.fraud_score);

  const timeAgo = transaction.timestamp
    ? formatDistanceToNow(new Date(transaction.timestamp), { addSuffix: true })
    : 'Just now';

  return (
    <div
      onClick={onClick}
      className={`p-4 rounded-lg border transition-all cursor-pointer hover:shadow-md ${
        transaction.is_fraud
          ? 'bg-red-50 border-red-200 hover:bg-red-100'
          : 'bg-white border-gray-200 hover:bg-gray-50'
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-mono text-gray-500 truncate">
              ID: {transaction.transaction_id.slice(0, 8)}...
            </span>
            {transaction.is_blocked && (
              <span className="px-2 py-0.5 text-xs font-semibold bg-red-600 text-white rounded">
                BLOCKED
              </span>
            )}
          </div>

          {/* Merchant and Amount */}
          <div className="flex items-baseline gap-2 mb-2">
            <span className="text-lg font-semibold text-gray-900">
              ${transaction.amount.toFixed(2)}
            </span>
            <span className="text-sm text-gray-600">
              @ {transaction.merchant_name}
            </span>
          </div>

          {/* Risk Info */}
          <div className="flex items-center gap-3">
            <span
              className={`px-2 py-1 text-xs font-medium border rounded ${riskBadgeStyles}`}
            >
              {transaction.risk_level.toUpperCase()} RISK
            </span>
            <span className={`text-sm font-bold ${scoreColor}`}>
              Score: {transaction.fraud_score.toFixed(1)}
            </span>
            {transaction.processing_time_ms && (
              <span className="text-xs text-gray-500">
                {transaction.processing_time_ms.toFixed(0)}ms
              </span>
            )}
          </div>
        </div>

        {/* Right side - Fraud indicator */}
        <div className="ml-4 flex flex-col items-end gap-1">
          {transaction.is_fraud ? (
            <svg
              className="w-8 h-8 text-red-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          ) : (
            <svg
              className="w-8 h-8 text-green-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          )}
          <span className="text-xs text-gray-500">{timeAgo}</span>
        </div>
      </div>
    </div>
  );
};
