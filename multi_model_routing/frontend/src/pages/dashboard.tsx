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
import {
  DollarSign,
  TrendingDown,
  Zap,
  Activity,
  AlertCircle,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, Badge } from '../components/ui'
import {
  getCostAnalytics,
  getSavingsAnalytics,
  getBudgetStatus,
  getRealtimeStats,
} from '../lib/api'

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

const TIER_COLORS = {
  frontier: '#ef4444',
  standard: '#3b82f6',
  fast: '#10b981',
}

export default function Dashboard() {
  const { data: costs } = useQuery({
    queryKey: ['costs', 'monthly'],
    queryFn: () => getCostAnalytics('monthly'),
  })

  const { data: savings } = useQuery({
    queryKey: ['savings', 'monthly'],
    queryFn: () => getSavingsAnalytics('monthly'),
  })

  const { data: budget } = useQuery({
    queryKey: ['budget'],
    queryFn: getBudgetStatus,
  })

  const { data: realtime } = useQuery({
    queryKey: ['realtime'],
    queryFn: getRealtimeStats,
    refetchInterval: 5000,
  })

  const tierData = costs?.cost_by_tier
    ? Object.entries(costs.cost_by_tier).map(([tier, cost]) => ({
        name: tier.charAt(0).toUpperCase() + tier.slice(1),
        value: cost,
        color: TIER_COLORS[tier as keyof typeof TIER_COLORS] || '#6b7280',
      }))
    : []

  const requestsByTierData = realtime?.requests_by_tier
    ? Object.entries(realtime.requests_by_tier).map(([tier, count]) => ({
        tier: tier.charAt(0).toUpperCase() + tier.slice(1),
        requests: count,
      }))
    : []

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">
          Monitor your LLM routing performance and costs
        </p>
      </div>

      {/* Stats Grid */}
      <div className="mb-8 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Cost (30d)"
          value={`$${costs?.total_cost?.toFixed(2) || '0.00'}`}
          icon={<DollarSign className="h-5 w-5" />}
          trend={costs?.total_requests ? `${costs.total_requests} requests` : undefined}
        />
        <StatCard
          title="Savings"
          value={`$${savings?.savings?.toFixed(2) || '0.00'}`}
          icon={<TrendingDown className="h-5 w-5" />}
          trend={
            savings?.savings_percentage
              ? `${savings.savings_percentage.toFixed(1)}% saved`
              : undefined
          }
          trendUp
        />
        <StatCard
          title="Avg Latency"
          value={`${realtime?.recent_avg_latency_ms?.toFixed(0) || '0'}ms`}
          icon={<Zap className="h-5 w-5" />}
        />
        <StatCard
          title="Total Requests"
          value={realtime?.total_requests?.toLocaleString() || '0'}
          icon={<Activity className="h-5 w-5" />}
        />
      </div>

      {/* Budget Alerts */}
      {budget?.alerts && budget.alerts.length > 0 && (
        <Card className="mb-8 border-yellow-200 bg-yellow-50">
          <CardContent className="flex items-start gap-3 py-4">
            <AlertCircle className="h-5 w-5 text-yellow-600" />
            <div>
              <h4 className="font-medium text-yellow-800">Budget Alerts</h4>
              <ul className="mt-1 text-sm text-yellow-700">
                {budget.alerts.map((alert, i) => (
                  <li key={i}>{alert}</li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Cost by Tier */}
        <Card>
          <CardHeader>
            <CardTitle>Cost by Tier</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              {tierData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={tierData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                      label={renderOuterLabel}
                      labelLine={{ stroke: '#9ca3af', strokeWidth: 1 }}
                    >
                      {tierData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value: number) => `$${value.toFixed(4)}`}
                    />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full items-center justify-center text-gray-500">
                  No data available
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Requests by Tier */}
        <Card>
          <CardHeader>
            <CardTitle>Requests by Tier</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              {requestsByTierData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={requestsByTierData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="tier" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="requests" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full items-center justify-center text-gray-500">
                  No data available
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Budget Status */}
        <Card>
          <CardHeader>
            <CardTitle>Budget Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <BudgetBar
                label="Daily"
                spent={budget?.daily_spent || 0}
                limit={budget?.daily_limit || 100}
              />
              <BudgetBar
                label="Weekly"
                spent={budget?.weekly_spent || 0}
                limit={budget?.weekly_limit || 500}
              />
              <BudgetBar
                label="Monthly"
                spent={budget?.monthly_spent || 0}
                limit={budget?.monthly_limit || 2000}
              />
            </div>
          </CardContent>
        </Card>

        {/* Recent Requests */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Requests</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {realtime?.recent_requests?.slice(0, 5).map((req, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-lg bg-gray-50 p-3"
                >
                  <div>
                    <span className="font-medium text-gray-900">{req.model}</span>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
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
                      <span>{req.latency_ms}ms</span>
                    </div>
                  </div>
                  <span className="font-medium text-gray-900">
                    ${req.cost.toFixed(4)}
                  </span>
                </div>
              )) || (
                <div className="text-center text-gray-500">No recent requests</div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

interface StatCardProps {
  title: string
  value: string
  icon: React.ReactNode
  trend?: string
  trendUp?: boolean
}

function StatCard({ title, value, icon, trend, trendUp }: StatCardProps) {
  return (
    <Card>
      <CardContent>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="mt-1 text-2xl font-bold text-gray-900">{value}</p>
            {trend && (
              <p
                className={`mt-1 text-sm ${
                  trendUp ? 'text-green-600' : 'text-gray-500'
                }`}
              >
                {trend}
              </p>
            )}
          </div>
          <div className="rounded-lg bg-blue-50 p-3 text-blue-600">{icon}</div>
        </div>
      </CardContent>
    </Card>
  )
}

interface BudgetBarProps {
  label: string
  spent: number
  limit: number
}

function BudgetBar({ label, spent, limit }: BudgetBarProps) {
  const percentage = limit > 0 ? Math.min((spent / limit) * 100, 100) : 0
  const color =
    percentage >= 90 ? 'bg-red-500' : percentage >= 75 ? 'bg-yellow-500' : 'bg-green-500'

  return (
    <div>
      <div className="mb-1 flex justify-between text-sm">
        <span className="font-medium text-gray-700">{label}</span>
        <span className="text-gray-500">
          ${spent.toFixed(2)} / ${limit.toFixed(2)}
        </span>
      </div>
      <div className="h-2 w-full rounded-full bg-gray-200">
        <div
          className={`h-2 rounded-full ${color}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
