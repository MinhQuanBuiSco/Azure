import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, Button } from '../components/ui'
import { getBudgetStatus, updateBudget, healthCheck } from '../lib/api'

export default function SettingsPage() {
  const queryClient = useQueryClient()

  const { data: budget } = useQuery({
    queryKey: ['budget'],
    queryFn: getBudgetStatus,
  })

  const { data: health, isLoading: healthLoading, refetch: refetchHealth } = useQuery({
    queryKey: ['health'],
    queryFn: healthCheck,
  })

  const [dailyLimit, setDailyLimit] = useState<string>('')
  const [weeklyLimit, setWeeklyLimit] = useState<string>('')
  const [monthlyLimit, setMonthlyLimit] = useState<string>('')
  const [hardLimit, setHardLimit] = useState<boolean>(true)
  const [formInitialized, setFormInitialized] = useState(false)

  // Initialize form when budget data loads
  if (budget && !formInitialized) {
    setDailyLimit(budget.daily_limit.toString())
    setWeeklyLimit(budget.weekly_limit.toString())
    setMonthlyLimit(budget.monthly_limit.toString())
    setFormInitialized(true)
  }

  const updateMutation = useMutation({
    mutationFn: updateBudget,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budget'] })
    },
  })

  const handleSave = () => {
    updateMutation.mutate({
      daily_limit: parseFloat(dailyLimit) || undefined,
      weekly_limit: parseFloat(weeklyLimit) || undefined,
      monthly_limit: parseFloat(monthlyLimit) || undefined,
      hard_limit: hardLimit,
    })
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600">Configure budget limits and system settings</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Budget Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Budget Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Daily Limit ($)
                </label>
                <input
                  type="number"
                  value={dailyLimit}
                  onChange={(e) => setDailyLimit(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="100.00"
                  step="0.01"
                  min="0"
                />
                {budget && (
                  <p className="mt-1 text-sm text-gray-500">
                    Current spend: ${budget.daily_spent.toFixed(2)}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Weekly Limit ($)
                </label>
                <input
                  type="number"
                  value={weeklyLimit}
                  onChange={(e) => setWeeklyLimit(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="500.00"
                  step="0.01"
                  min="0"
                />
                {budget && (
                  <p className="mt-1 text-sm text-gray-500">
                    Current spend: ${budget.weekly_spent.toFixed(2)}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Monthly Limit ($)
                </label>
                <input
                  type="number"
                  value={monthlyLimit}
                  onChange={(e) => setMonthlyLimit(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="2000.00"
                  step="0.01"
                  min="0"
                />
                {budget && (
                  <p className="mt-1 text-sm text-gray-500">
                    Current spend: ${budget.monthly_spent.toFixed(2)}
                  </p>
                )}
              </div>

              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="hardLimit"
                  checked={hardLimit}
                  onChange={(e) => setHardLimit(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="hardLimit" className="text-sm text-gray-700">
                  Enforce hard limits (block requests when budget exceeded)
                </label>
              </div>

              <div className="flex gap-3 pt-4">
                <Button
                  onClick={handleSave}
                  isLoading={updateMutation.isPending}
                >
                  <Save className="mr-2 h-4 w-4" />
                  Save Changes
                </Button>
                {updateMutation.isSuccess && (
                  <span className="flex items-center text-sm text-green-600">
                    <CheckCircle className="mr-1 h-4 w-4" />
                    Saved
                  </span>
                )}
                {updateMutation.isError && (
                  <span className="flex items-center text-sm text-red-600">
                    <AlertCircle className="mr-1 h-4 w-4" />
                    Failed to save
                  </span>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* System Status */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>System Status</CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => refetchHealth()}
              disabled={healthLoading}
            >
              <RefreshCw
                className={`h-4 w-4 ${healthLoading ? 'animate-spin' : ''}`}
              />
            </Button>
          </CardHeader>
          <CardContent>
            {health ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Overall Status</span>
                  <StatusBadge status={health.status} />
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Version</span>
                  <span className="font-medium text-gray-900">{health.version}</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Environment</span>
                  <span className="font-medium text-gray-900">
                    {health.environment}
                  </span>
                </div>

                {health.services && (
                  <div className="border-t border-gray-200 pt-4">
                    <span className="text-sm font-medium text-gray-700">
                      Services
                    </span>
                    <div className="mt-2 space-y-2">
                      {Object.entries(health.services).map(([service, status]) => (
                        <div
                          key={service}
                          className="flex items-center justify-between"
                        >
                          <span className="text-sm text-gray-600 capitalize">
                            {service}
                          </span>
                          <ServiceStatus healthy={status} />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : healthLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="h-6 animate-pulse rounded bg-gray-200"
                  />
                ))}
              </div>
            ) : (
              <div className="text-center text-gray-500">
                Unable to fetch system status
              </div>
            )}
          </CardContent>
        </Card>

        {/* Model Pricing Reference */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Model Pricing Reference</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="pb-3 text-left text-sm font-medium text-gray-600">
                      Tier
                    </th>
                    <th className="pb-3 text-left text-sm font-medium text-gray-600">
                      Models
                    </th>
                    <th className="pb-3 text-right text-sm font-medium text-gray-600">
                      Input ($/1M tokens)
                    </th>
                    <th className="pb-3 text-right text-sm font-medium text-gray-600">
                      Output ($/1M tokens)
                    </th>
                    <th className="pb-3 text-left text-sm font-medium text-gray-600">
                      Use Case
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-gray-100">
                    <td className="py-3">
                      <span className="rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800">
                        Frontier
                      </span>
                    </td>
                    <td className="py-3 text-gray-900">GPT-4.1</td>
                    <td className="py-3 text-right text-gray-900">$2.00</td>
                    <td className="py-3 text-right text-gray-900">$8.00</td>
                    <td className="py-3 text-gray-600">Complex reasoning, research</td>
                  </tr>
                  <tr className="border-b border-gray-100">
                    <td className="py-3">
                      <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
                        Standard
                      </span>
                    </td>
                    <td className="py-3 text-gray-900">GPT-4.1 Mini</td>
                    <td className="py-3 text-right text-gray-900">$0.40</td>
                    <td className="py-3 text-right text-gray-900">$1.60</td>
                    <td className="py-3 text-gray-600">General tasks, coding</td>
                  </tr>
                  <tr>
                    <td className="py-3">
                      <span className="rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                        Fast
                      </span>
                    </td>
                    <td className="py-3 text-gray-900">GPT-4.1 Nano</td>
                    <td className="py-3 text-right text-gray-900">$0.10</td>
                    <td className="py-3 text-right text-gray-900">$0.40</td>
                    <td className="py-3 text-gray-600">Simple queries, chat</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const variants: Record<string, { bg: string; text: string }> = {
    healthy: { bg: 'bg-green-100', text: 'text-green-800' },
    degraded: { bg: 'bg-yellow-100', text: 'text-yellow-800' },
    unhealthy: { bg: 'bg-red-100', text: 'text-red-800' },
  }

  const { bg, text } = variants[status] || variants.unhealthy

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${bg} ${text}`}
    >
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  )
}

function ServiceStatus({ healthy }: { healthy: boolean }) {
  return healthy ? (
    <span className="flex items-center text-sm text-green-600">
      <CheckCircle className="mr-1 h-4 w-4" />
      Connected
    </span>
  ) : (
    <span className="flex items-center text-sm text-red-600">
      <AlertCircle className="mr-1 h-4 w-4" />
      Disconnected
    </span>
  )
}
