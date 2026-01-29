import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { TrendingDown, DollarSign, Activity, Clock } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, Select, Badge } from '../components/ui'
import { getCostAnalytics, getSavingsAnalytics, getRealtimeStats } from '../lib/api'

const COLORS = ['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6']

const RADIAN = Math.PI / 180

function renderOuterLabel({
  cx,
  cy,
  midAngle,
  outerRadius,
  name,
  value,
  fill,
}: any) {
  const radius = outerRadius + 25
  const x = cx + radius * Math.cos(-midAngle * RADIAN)
  const y = cy + radius * Math.sin(-midAngle * RADIAN)

  return (
    <text
      x={x}
      y={y}
      fill={fill}
      textAnchor={x > cx ? 'start' : 'end'}
      dominantBaseline="central"
      fontSize={12}
    >
      {`${name}: $${value.toFixed(2)}`}
    </text>
  )
}

type Period = 'daily' | 'weekly' | 'monthly'

export default function Analytics() {
  const [period, setPeriod] = useState<Period>('monthly')

  const { data: costs, isLoading: costsLoading } = useQuery({
    queryKey: ['costs', period],
    queryFn: () => getCostAnalytics(period),
  })

  const { data: savings, isLoading: savingsLoading } = useQuery({
    queryKey: ['savings', period],
    queryFn: () => getSavingsAnalytics(period),
  })

  const { data: realtime } = useQuery({
    queryKey: ['realtime'],
    queryFn: getRealtimeStats,
    refetchInterval: 10000,
  })

  const modelData = costs?.cost_by_model
    ? Object.entries(costs.cost_by_model).map(([model, cost], i) => ({
        name: model,
        cost,
        color: COLORS[i % COLORS.length],
      }))
    : []

  const tierData = costs?.cost_by_tier
    ? Object.entries(costs.cost_by_tier).map(([tier, cost]) => ({
        tier: tier.charAt(0).toUpperCase() + tier.slice(1),
        cost,
      }))
    : []

  const savingsComparison = savings
    ? [
        { name: 'Actual Cost', value: savings.actual_cost, fill: '#10b981' },
        { name: 'Would Have Cost', value: savings.frontier_cost, fill: '#ef4444' },
      ]
    : []

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600">Detailed cost and savings analysis</p>
        </div>
        <Select
          value={period}
          onChange={(e) => setPeriod(e.target.value as Period)}
          className="w-40"
        >
          <option value="daily">Last 24 hours</option>
          <option value="weekly">Last 7 days</option>
          <option value="monthly">Last 30 days</option>
        </Select>
      </div>

      {/* Summary Stats */}
      <div className="mb-8 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Cost"
          value={`$${costs?.total_cost?.toFixed(2) || '0.00'}`}
          subtitle={`${costs?.total_requests || 0} requests`}
          icon={<DollarSign className="h-5 w-5" />}
          loading={costsLoading}
        />
        <StatCard
          title="Total Savings"
          value={`$${savings?.savings?.toFixed(2) || '0.00'}`}
          subtitle={`${savings?.savings_percentage?.toFixed(1) || 0}% saved`}
          icon={<TrendingDown className="h-5 w-5" />}
          positive
          loading={savingsLoading}
        />
        <StatCard
          title="Avg Cost/Request"
          value={`$${costs?.average_cost_per_request?.toFixed(4) || '0.0000'}`}
          subtitle="per request"
          icon={<Activity className="h-5 w-5" />}
          loading={costsLoading}
        />
        <StatCard
          title="Lower Tier Routes"
          value={`${savings?.requests_routed_to_lower_tiers || 0}`}
          subtitle={`of ${savings?.total_requests || 0} total`}
          icon={<Clock className="h-5 w-5" />}
          loading={savingsLoading}
        />
      </div>

      {/* Charts Row 1 */}
      <div className="mb-6 grid gap-6 lg:grid-cols-2">
        {/* Savings Comparison */}
        <Card>
          <CardHeader>
            <CardTitle>Cost Savings Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              {savingsComparison.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={savingsComparison}
                    layout="vertical"
                    margin={{ left: 20 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" tickFormatter={(v) => `$${v.toFixed(2)}`} />
                    <YAxis type="category" dataKey="name" width={120} />
                    <Tooltip formatter={(value: number) => `$${value.toFixed(4)}`} />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                      {savingsComparison.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState />
              )}
            </div>
            {savings && (
              <div className="mt-4 rounded-lg bg-green-50 p-4">
                <div className="flex items-center gap-2">
                  <TrendingDown className="h-5 w-5 text-green-600" />
                  <span className="font-medium text-green-800">
                    You saved ${savings.savings.toFixed(2)} (
                    {savings.savings_percentage.toFixed(1)}%)
                  </span>
                </div>
                <p className="mt-1 text-sm text-green-700">
                  By using intelligent routing instead of always using frontier models
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Cost by Tier */}
        <Card>
          <CardHeader>
            <CardTitle>Cost Distribution by Tier</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              {tierData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={tierData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="tier" />
                    <YAxis tickFormatter={(v) => `$${v.toFixed(2)}`} />
                    <Tooltip formatter={(value: number) => `$${value.toFixed(4)}`} />
                    <Bar dataKey="cost" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState />
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="mb-6 grid gap-6 lg:grid-cols-2">
        {/* Cost by Model */}
        <Card>
          <CardHeader>
            <CardTitle>Cost by Model</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              {modelData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={modelData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="cost"
                      label={renderOuterLabel}
                      labelLine={{ stroke: '#9ca3af', strokeWidth: 1 }}
                    >
                      {modelData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value: number) => `$${value.toFixed(4)}`}
                    />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState />
              )}
            </div>
          </CardContent>
        </Card>

        {/* Model Usage Table */}
        <Card>
          <CardHeader>
            <CardTitle>Model Usage Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="pb-3 text-left text-sm font-medium text-gray-600">
                      Model
                    </th>
                    <th className="pb-3 text-right text-sm font-medium text-gray-600">
                      Cost
                    </th>
                    <th className="pb-3 text-right text-sm font-medium text-gray-600">
                      % of Total
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {modelData.map((model, i) => (
                    <tr key={i} className="border-b border-gray-100">
                      <td className="py-3">
                        <div className="flex items-center gap-2">
                          <div
                            className="h-3 w-3 rounded-full"
                            style={{ backgroundColor: model.color }}
                          />
                          <span className="font-medium text-gray-900">
                            {model.name}
                          </span>
                        </div>
                      </td>
                      <td className="py-3 text-right font-medium text-gray-900">
                        ${model.cost.toFixed(4)}
                      </td>
                      <td className="py-3 text-right text-gray-600">
                        {costs?.total_cost
                          ? ((model.cost / costs.total_cost) * 100).toFixed(1)
                          : 0}
                        %
                      </td>
                    </tr>
                  ))}
                  {modelData.length === 0 && (
                    <tr>
                      <td colSpan={3} className="py-8 text-center text-gray-500">
                        No model usage data available
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Requests</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="pb-3 text-left text-sm font-medium text-gray-600">
                    Timestamp
                  </th>
                  <th className="pb-3 text-left text-sm font-medium text-gray-600">
                    Model
                  </th>
                  <th className="pb-3 text-left text-sm font-medium text-gray-600">
                    Tier
                  </th>
                  <th className="pb-3 text-right text-sm font-medium text-gray-600">
                    Latency
                  </th>
                  <th className="pb-3 text-right text-sm font-medium text-gray-600">
                    Cost
                  </th>
                </tr>
              </thead>
              <tbody>
                {realtime?.recent_requests?.slice(0, 10).map((req, i) => (
                  <tr key={i} className="border-b border-gray-100">
                    <td className="py-3 text-sm text-gray-600">
                      {new Date(req.timestamp).toLocaleString()}
                    </td>
                    <td className="py-3 font-medium text-gray-900">{req.model}</td>
                    <td className="py-3">
                      <Badge
                        variant={
                          req.tier === 'frontier'
                            ? 'danger'
                            : req.tier === 'standard'
                            ? 'info'
                            : 'success'
                        }
                      >
                        {req.tier}
                      </Badge>
                    </td>
                    <td className="py-3 text-right text-gray-600">
                      {req.latency_ms}ms
                    </td>
                    <td className="py-3 text-right font-medium text-gray-900">
                      ${req.cost.toFixed(6)}
                    </td>
                  </tr>
                ))}
                {(!realtime?.recent_requests ||
                  realtime.recent_requests.length === 0) && (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-gray-500">
                      No recent requests
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

interface StatCardProps {
  title: string
  value: string
  subtitle: string
  icon: React.ReactNode
  positive?: boolean
  loading?: boolean
}

function StatCard({
  title,
  value,
  subtitle,
  icon,
  positive,
  loading,
}: StatCardProps) {
  return (
    <Card>
      <CardContent>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            {loading ? (
              <div className="mt-1 h-8 w-24 animate-pulse rounded bg-gray-200" />
            ) : (
              <p className="mt-1 text-2xl font-bold text-gray-900">{value}</p>
            )}
            <p
              className={`mt-1 text-sm ${
                positive ? 'text-green-600' : 'text-gray-500'
              }`}
            >
              {subtitle}
            </p>
          </div>
          <div
            className={`rounded-lg p-3 ${
              positive ? 'bg-green-50 text-green-600' : 'bg-blue-50 text-blue-600'
            }`}
          >
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function EmptyState() {
  return (
    <div className="flex h-full items-center justify-center text-gray-500">
      No data available
    </div>
  )
}
