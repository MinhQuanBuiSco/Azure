/**
 * Analytics page with fraud detection metrics and visualizations
 * Uses real data from backend API
 */
import { useState } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../lib/api-client';
import { useTheme } from '../contexts/ThemeContext';

// Types for API responses
interface DashboardMetrics {
  total_transactions_today: number;
  fraud_detected: number;
  fraud_rate: number;
  total_amount_blocked: number;
  alerts_pending: number;
  average_processing_time_ms: number;
}

interface TrendDataPoint {
  date: string;
  day: string;
  transactions: number;
  fraud: number;
  blocked: number;
}

interface TrendsResponse {
  period_days: number;
  data_points: TrendDataPoint[];
}

interface HourlyDataPoint {
  hour: string;
  transactions: number;
  fraud: number;
  fraudRate: number;
}

interface HourlyResponse {
  date: string;
  data_points: HourlyDataPoint[];
}

interface RiskDistributionItem {
  name: string;
  value: number;
  color: string;
}

interface RiskDistributionResponse {
  period_days: number;
  distribution: RiskDistributionItem[];
}

interface MerchantFraudItem {
  category: string;
  total: number;
  fraud: number;
}

interface MerchantFraudResponse {
  period_days: number;
  categories: MerchantFraudItem[];
}

interface ScoreDistributionItem {
  range: string;
  count: number;
}

interface ScoreDistributionResponse {
  period_days: number;
  distribution: ScoreDistributionItem[];
}

type TimeRange = '7d' | '30d' | '90d';

const timeRangeToDays: Record<TimeRange, number> = {
  '7d': 7,
  '30d': 30,
  '90d': 90,
};

export default function Analytics() {
  const [timeRange, setTimeRange] = useState<TimeRange>('7d');
  const days = timeRangeToDays[timeRange];
  const { theme } = useTheme();

  // Chart colors based on theme
  const chartColors = {
    grid: theme === 'dark' ? '#374151' : '#e5e7eb',
    axis: theme === 'dark' ? '#9ca3af' : '#6b7280',
    tooltipBg: theme === 'dark' ? '#1f2937' : '#fff',
    tooltipBorder: theme === 'dark' ? '#374151' : '#e5e7eb',
  };

  // Fetch dashboard metrics
  const { data: dashboard, isLoading: dashboardLoading } = useQuery<DashboardMetrics>({
    queryKey: ['analytics', 'dashboard'],
    queryFn: async () => {
      const response = await apiClient.get<DashboardMetrics>('/api/v1/analytics/dashboard');
      return response.data;
    },
    refetchInterval: 30000,
  });

  // Fetch trends data
  const { data: trends, isLoading: trendsLoading } = useQuery<TrendsResponse>({
    queryKey: ['analytics', 'trends', days],
    queryFn: async () => {
      const response = await apiClient.get<TrendsResponse>(`/api/v1/analytics/trends?days=${days}`);
      return response.data;
    },
    refetchInterval: 60000,
  });

  // Fetch hourly data
  const { data: hourly, isLoading: hourlyLoading } = useQuery<HourlyResponse>({
    queryKey: ['analytics', 'hourly'],
    queryFn: async () => {
      const response = await apiClient.get<HourlyResponse>('/api/v1/analytics/hourly');
      return response.data;
    },
    refetchInterval: 60000,
  });

  // Fetch risk distribution
  const { data: riskDistribution, isLoading: riskLoading } = useQuery<RiskDistributionResponse>({
    queryKey: ['analytics', 'risk-distribution'],
    queryFn: async () => {
      const response = await apiClient.get<RiskDistributionResponse>('/api/v1/analytics/risk-distribution');
      return response.data;
    },
    refetchInterval: 60000,
  });

  // Fetch merchant fraud stats
  const { data: merchantFraud, isLoading: merchantLoading } = useQuery<MerchantFraudResponse>({
    queryKey: ['analytics', 'merchant-fraud'],
    queryFn: async () => {
      const response = await apiClient.get<MerchantFraudResponse>('/api/v1/analytics/merchant-fraud');
      return response.data;
    },
    refetchInterval: 60000,
  });

  // Fetch score distribution
  const { data: scoreDistribution, isLoading: scoreLoading } = useQuery<ScoreDistributionResponse>({
    queryKey: ['analytics', 'score-distribution'],
    queryFn: async () => {
      const response = await apiClient.get<ScoreDistributionResponse>('/api/v1/analytics/score-distribution');
      return response.data;
    },
    refetchInterval: 60000,
  });

  // Loading skeleton component
  const LoadingSkeleton = ({ height = 300 }: { height?: number }) => (
    <div
      className="animate-pulse bg-muted rounded-lg"
      style={{ height }}
    />
  );

  // Calculate summary from dashboard data
  const totalTransactions = dashboard?.total_transactions_today ?? 0;
  const totalFraud = dashboard?.fraud_detected ?? 0;
  const fraudRate = dashboard?.fraud_rate ?? 0;
  const totalBlocked = dashboard?.alerts_pending ?? 0;

  return (
    <div className="flex-1 space-y-6 p-8 pt-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-foreground">Analytics</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Fraud detection metrics and insights
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as TimeRange)}
            className="px-4 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-card text-card-foreground"
          >
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="bg-card rounded-2xl border border-border shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Transactions</p>
              {dashboardLoading ? (
                <div className="h-8 w-24 bg-muted animate-pulse rounded mt-2" />
              ) : (
                <p className="text-2xl font-bold text-card-foreground mt-2">
                  {totalTransactions.toLocaleString()}
                </p>
              )}
            </div>
            <div className="p-3 bg-primary/10 rounded-xl">
              <svg
                className="w-6 h-6 text-primary"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-card rounded-2xl border border-destructive/20 shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Fraud Detected</p>
              {dashboardLoading ? (
                <div className="h-8 w-16 bg-muted animate-pulse rounded mt-2" />
              ) : (
                <p className="text-2xl font-bold text-destructive mt-2">{totalFraud}</p>
              )}
            </div>
            <div className="p-3 bg-destructive/10 rounded-xl">
              <svg
                className="w-6 h-6 text-destructive"
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
            </div>
          </div>
        </div>

        <div className="bg-card rounded-2xl border border-warning/20 shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Fraud Rate</p>
              {dashboardLoading ? (
                <div className="h-8 w-20 bg-muted animate-pulse rounded mt-2" />
              ) : (
                <p className="text-2xl font-bold text-warning mt-2">{fraudRate}%</p>
              )}
            </div>
            <div className="p-3 bg-warning/10 rounded-xl">
              <svg
                className="w-6 h-6 text-warning"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-card rounded-2xl border border-success/20 shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Blocked</p>
              {dashboardLoading ? (
                <div className="h-8 w-16 bg-muted animate-pulse rounded mt-2" />
              ) : (
                <p className="text-2xl font-bold text-success mt-2">{totalBlocked}</p>
              )}
            </div>
            <div className="p-3 bg-success/10 rounded-xl">
              <svg
                className="w-6 h-6 text-success"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Fraud Trends Over Time */}
        <div className="bg-card rounded-2xl border border-border shadow-sm p-6">
          <h3 className="text-lg font-semibold text-card-foreground mb-4">
            Transaction & Fraud Trends
          </h3>
          {trendsLoading ? (
            <LoadingSkeleton />
          ) : trends?.data_points && trends.data_points.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trends.data_points}>
                <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                <XAxis dataKey="day" stroke={chartColors.axis} />
                <YAxis stroke={chartColors.axis} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: chartColors.tooltipBg,
                    border: `1px solid ${chartColors.tooltipBorder}`,
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="transactions"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="Total Transactions"
                />
                <Line
                  type="monotone"
                  dataKey="fraud"
                  stroke="#ef4444"
                  strokeWidth={2}
                  name="Fraud Detected"
                />
                <Line
                  type="monotone"
                  dataKey="blocked"
                  stroke="#10b981"
                  strokeWidth={2}
                  name="Blocked"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[300px] text-muted-foreground">
              No trend data available for this period
            </div>
          )}
        </div>

        {/* Risk Distribution */}
        <div className="bg-card rounded-2xl border border-border shadow-sm p-6">
          <h3 className="text-lg font-semibold text-card-foreground mb-4">
            Risk Level Distribution
          </h3>
          {riskLoading ? (
            <LoadingSkeleton />
          ) : riskDistribution?.distribution && riskDistribution.distribution.some(d => d.value > 0) ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={riskDistribution.distribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) =>
                    percent > 0 ? `${name}: ${(percent * 100).toFixed(0)}%` : ''
                  }
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {riskDistribution.distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[300px] text-muted-foreground">
              No risk distribution data available
            </div>
          )}
        </div>

        {/* Fraud by Merchant Category */}
        <div className="bg-card rounded-2xl border border-border shadow-sm p-6">
          <h3 className="text-lg font-semibold text-card-foreground mb-4">
            Fraud by Merchant
          </h3>
          {merchantLoading ? (
            <LoadingSkeleton />
          ) : merchantFraud?.categories && merchantFraud.categories.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={merchantFraud.categories}>
                <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                <XAxis dataKey="category" stroke={chartColors.axis} angle={-45} textAnchor="end" height={100} />
                <YAxis stroke={chartColors.axis} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: chartColors.tooltipBg,
                    border: `1px solid ${chartColors.tooltipBorder}`,
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Bar dataKey="total" fill="#3b82f6" name="Total Transactions" />
                <Bar dataKey="fraud" fill="#ef4444" name="Fraud Detected" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[300px] text-muted-foreground">
              No merchant data available
            </div>
          )}
        </div>

        {/* Fraud Score Distribution */}
        <div className="bg-card rounded-2xl border border-border shadow-sm p-6">
          <h3 className="text-lg font-semibold text-card-foreground mb-4">
            Fraud Score Distribution
          </h3>
          {scoreLoading ? (
            <LoadingSkeleton />
          ) : scoreDistribution?.distribution && scoreDistribution.distribution.some(d => d.count > 0) ? (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={scoreDistribution.distribution}>
                <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                <XAxis dataKey="range" stroke={chartColors.axis} />
                <YAxis stroke={chartColors.axis} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: chartColors.tooltipBg,
                    border: `1px solid ${chartColors.tooltipBorder}`,
                    borderRadius: '8px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="count"
                  stroke="#8b5cf6"
                  fill="#8b5cf6"
                  fillOpacity={0.6}
                  name="Transaction Count"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[300px] text-muted-foreground">
              No score distribution data available
            </div>
          )}
        </div>
      </div>

      {/* Hourly Fraud Rate */}
      <div className="bg-card rounded-2xl border border-border shadow-sm p-6">
        <h3 className="text-lg font-semibold text-card-foreground mb-4">
          Hourly Transaction Volume & Fraud Rate (Today)
        </h3>
        {hourlyLoading ? (
          <LoadingSkeleton />
        ) : hourly?.data_points && hourly.data_points.some(d => d.transactions > 0) ? (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={hourly.data_points}>
              <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
              <XAxis dataKey="hour" stroke={chartColors.axis} />
              <YAxis stroke={chartColors.axis} />
              <Tooltip
                contentStyle={{
                  backgroundColor: chartColors.tooltipBg,
                  border: `1px solid ${chartColors.tooltipBorder}`,
                  borderRadius: '8px',
                }}
              />
              <Legend />
              <Area
                type="monotone"
                dataKey="transactions"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.3}
                name="Transactions"
              />
              <Area
                type="monotone"
                dataKey="fraudRate"
                stroke="#ef4444"
                fill="#ef4444"
                fillOpacity={0.3}
                name="Fraud Rate (%)"
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-[300px] text-muted-foreground">
            No hourly data available for today
          </div>
        )}
      </div>
    </div>
  );
}
