/**
 * Transaction detail page with comprehensive risk breakdown
 */
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../lib/api-client';

interface TransactionDetail {
  id: string;
  user_id: string;
  amount: number;
  currency: string;
  merchant_name: string;
  merchant_category: string;
  transaction_type: string;
  country: string;
  city: string;
  latitude: number;
  longitude: number;
  device_id: string;
  ip_address: string;
  fraud_score: number;
  risk_level: string;
  is_fraud: boolean;
  is_blocked: boolean;
  triggered_rules: string[];
  rule_scores: Record<string, number>;
  anomaly_score: number;
  azure_score: number;
  explanation: string;
  processing_time_ms: number;
  model_version: string;
  transaction_time: string;
  created_at: string;
}

const getRiskColor = (score: number) => {
  if (score >= 70) return 'text-red-600';
  if (score >= 30) return 'text-yellow-600';
  return 'text-green-600';
};

const getRiskBgColor = (score: number) => {
  if (score >= 70) return 'bg-red-100 border-red-200';
  if (score >= 30) return 'bg-yellow-100 border-yellow-200';
  return 'bg-green-100 border-green-200';
};

export default function TransactionDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: transaction, isLoading, error } = useQuery<TransactionDetail>({
    queryKey: ['transaction', id],
    queryFn: async () => {
      const response = await apiClient.get(`/api/v1/transactions/${id}`);
      return response.data;
    },
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="flex-1 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading transaction...</p>
        </div>
      </div>
    );
  }

  if (error || !transaction) {
    return (
      <div className="flex-1 p-8">
        <div className="max-w-2xl mx-auto text-center py-12">
          <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Transaction Not Found</h3>
          <p className="text-gray-600 mb-4">The transaction you're looking for doesn't exist or has been removed.</p>
          <button
            onClick={() => navigate('/transactions')}
            className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800"
          >
            Back to Transactions
          </button>
        </div>
      </div>
    );
  }

  const ruleScorePercentage = Object.values(transaction.rule_scores).reduce((a, b) => a + b, 0);
  const mlPercentage = (transaction.anomaly_score / 100) * 25; // 25% weight
  const azurePercentage = (transaction.azure_score / 100) * 15; // 15% weight

  return (
    <div className="flex-1 p-8 pt-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back
        </button>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Transaction Details</h1>
            <p className="text-sm text-gray-500 mt-1 font-mono">ID: {transaction.id}</p>
          </div>
          <div className="flex items-center gap-3">
            {transaction.is_blocked && (
              <span className="px-3 py-1.5 bg-red-600 text-white rounded-lg font-semibold text-sm">
                BLOCKED
              </span>
            )}
            <span className={`px-3 py-1.5 rounded-lg font-semibold text-sm border ${getRiskBgColor(transaction.fraud_score)}`}>
              {transaction.risk_level.toUpperCase()} RISK
            </span>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column - Main Info */}
        <div className="lg:col-span-2 space-y-6">
          {/* Fraud Score Overview */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Fraud Risk Score</h2>
            <div className="flex items-center gap-4 mb-6">
              <div className="flex-1">
                <div className="flex items-baseline gap-2">
                  <span className={`text-5xl font-bold ${getRiskColor(transaction.fraud_score)}`}>
                    {transaction.fraud_score.toFixed(1)}
                  </span>
                  <span className="text-2xl text-gray-500">/ 100</span>
                </div>
                <p className="text-sm text-gray-600 mt-2">
                  {transaction.is_fraud ? 'Fraudulent Transaction Detected' : 'Transaction Appears Legitimate'}
                </p>
              </div>
              {transaction.is_fraud ? (
                <svg className="w-20 h-20 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              ) : (
                <svg className="w-20 h-20 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              )}
            </div>

            {/* Score Breakdown */}
            <div className="space-y-3">
              <div>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="font-medium text-gray-700">Rule Engine (60%)</span>
                  <span className="font-semibold">{ruleScorePercentage.toFixed(1)} points</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${(ruleScorePercentage / 60) * 100}%` }}></div>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="font-medium text-gray-700">Isolation Forest (25%)</span>
                  <span className="font-semibold">{transaction.anomaly_score.toFixed(1)}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-purple-500 h-2 rounded-full" style={{ width: `${transaction.anomaly_score}%` }}></div>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="font-medium text-gray-700">Azure Anomaly Detector (15%)</span>
                  <span className="font-semibold">{transaction.azure_score.toFixed(1)}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-cyan-500 h-2 rounded-full" style={{ width: `${transaction.azure_score}%` }}></div>
                </div>
              </div>
            </div>
          </div>

          {/* AI Explanation */}
          {transaction.explanation && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <div className="flex items-start gap-3">
                <svg className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="flex-1">
                  <h3 className="font-semibold text-blue-900 mb-2">AI Analysis</h3>
                  <p className="text-sm text-blue-800 whitespace-pre-line">{transaction.explanation}</p>
                </div>
              </div>
            </div>
          )}

          {/* Triggered Rules */}
          {transaction.triggered_rules.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Triggered Rules</h2>
              <div className="space-y-3">
                {transaction.triggered_rules.map((rule) => (
                  <div key={rule} className="flex items-start gap-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 text-sm">{rule.replace(/_/g, ' ').toUpperCase()}</p>
                      <p className="text-sm text-red-600 mt-1">Score: +{transaction.rule_scores[rule]?.toFixed(1) || 0}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Transaction Details */}
        <div className="space-y-6">
          {/* Transaction Info */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Transaction Info</h2>
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-gray-500">Amount</dt>
                <dd className="font-semibold text-gray-900 text-lg">${transaction.amount.toFixed(2)} {transaction.currency}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Merchant</dt>
                <dd className="font-medium text-gray-900">{transaction.merchant_name}</dd>
                <dd className="text-xs text-gray-500">{transaction.merchant_category}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Type</dt>
                <dd className="font-medium text-gray-900 capitalize">{transaction.transaction_type}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Time</dt>
                <dd className="font-medium text-gray-900">{new Date(transaction.transaction_time).toLocaleString()}</dd>
              </div>
            </dl>
          </div>

          {/* Location */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Location</h2>
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-gray-500">City</dt>
                <dd className="font-medium text-gray-900">{transaction.city}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Country</dt>
                <dd className="font-medium text-gray-900">{transaction.country}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Coordinates</dt>
                <dd className="font-mono text-xs text-gray-600">
                  {transaction.latitude?.toFixed(4)}, {transaction.longitude?.toFixed(4)}
                </dd>
              </div>
            </dl>
          </div>

          {/* Device Info */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Device Info</h2>
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-gray-500">Device ID</dt>
                <dd className="font-mono text-xs text-gray-900">{transaction.device_id}</dd>
              </div>
              <div>
                <dt className="text-gray-500">IP Address</dt>
                <dd className="font-mono text-xs text-gray-900">{transaction.ip_address}</dd>
              </div>
            </dl>
          </div>

          {/* Processing Info */}
          <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
            <dl className="space-y-2 text-xs text-gray-600">
              <div className="flex justify-between">
                <dt>Processing Time</dt>
                <dd className="font-mono">{transaction.processing_time_ms.toFixed(2)}ms</dd>
              </div>
              <div className="flex justify-between">
                <dt>Model Version</dt>
                <dd className="font-mono text-[10px]">{transaction.model_version}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}
