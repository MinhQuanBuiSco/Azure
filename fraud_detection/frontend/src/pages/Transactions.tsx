/**
 * Transactions list page
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../lib/api-client';

interface Transaction {
  id: string;
  user_id: string;
  amount: number;
  merchant_name: string;
  fraud_score: number;
  risk_level: string;
  is_fraud: boolean;
  is_blocked: boolean;
  transaction_time: string;
}

interface TransactionsResponse {
  transactions: Transaction[];
  total: number;
  skip: number;
  limit: number;
}

const getRiskBadge = (riskLevel: string) => {
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

export default function Transactions() {
  const navigate = useNavigate();
  const [riskFilter, setRiskFilter] = useState<string>('all');

  const { data, isLoading } = useQuery<TransactionsResponse>({
    queryKey: ['transactions', riskFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (riskFilter !== 'all') {
        params.append('risk_level', riskFilter);
      }
      const response = await apiClient.get(`/api/v1/transactions?${params.toString()}`);
      return response.data;
    },
  });

  return (
    <div className="flex-1 space-y-6 p-8 pt-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Transactions</h2>
          <p className="text-sm text-gray-500 mt-1">View and analyze transaction history</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Risk Levels</option>
            <option value="high">High Risk</option>
            <option value="medium">Medium Risk</option>
            <option value="low">Low Risk</option>
          </select>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading transactions...</p>
          </div>
        ) : !data || data.transactions.length === 0 ? (
          <div className="p-12 text-center">
            <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <p className="text-gray-600">No transactions found</p>
            <p className="text-sm text-gray-400 mt-2">
              Generate test transactions with <code className="px-2 py-1 bg-gray-100 rounded">make generate-txns</code>
            </p>
          </div>
        ) : (
          <>
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Merchant
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fraud Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Risk Level
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Time
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.transactions.map((txn) => (
                  <tr
                    key={txn.id}
                    onClick={() => navigate(`/transactions/${txn.id}`)}
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500">
                      {txn.id.slice(0, 8)}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                      ${txn.amount.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {txn.merchant_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`font-bold ${txn.fraud_score >= 70 ? 'text-red-600' : txn.fraud_score >= 30 ? 'text-yellow-600' : 'text-green-600'}`}>
                        {txn.fraud_score.toFixed(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 text-xs font-medium border rounded ${getRiskBadge(txn.risk_level)}`}>
                        {txn.risk_level.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {txn.is_blocked ? (
                        <span className="px-2 py-1 text-xs font-semibold bg-red-600 text-white rounded">
                          BLOCKED
                        </span>
                      ) : txn.is_fraud ? (
                        <span className="px-2 py-1 text-xs font-semibold bg-yellow-600 text-white rounded">
                          FRAUD
                        </span>
                      ) : (
                        <span className="px-2 py-1 text-xs font-semibold bg-green-600 text-white rounded">
                          OK
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(txn.transaction_time).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {data && (
              <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
                <p className="text-sm text-gray-600">
                  Showing {data.transactions.length} of {data.total} transactions
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
