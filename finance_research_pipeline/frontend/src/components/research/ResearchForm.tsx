import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Search, Sparkles, Building2, Calendar, Users } from 'lucide-react'
import { motion } from 'framer-motion'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import type { ResearchRequest, ResearchResponse, ResearchType } from '../../types/research'
import { RESEARCH_TYPE_OPTIONS } from '../../types/research'

interface ResearchFormProps {
  onResearchStart: (response: ResearchResponse) => void
}

async function startResearch(request: ResearchRequest): Promise<ResearchResponse> {
  // Use relative URL in production, VITE_API_URL for local dev
  const apiUrl = import.meta.env.VITE_API_URL || ''
  const response = await fetch(`${apiUrl}/api/v1/research/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    throw new Error('Failed to start research')
  }

  return response.json()
}

export default function ResearchForm({ onResearchStart }: ResearchFormProps) {
  const [companyName, setCompanyName] = useState('')
  const [tickerSymbol, setTickerSymbol] = useState('')
  const [researchType, setResearchType] = useState<ResearchType>('comprehensive')
  const [additionalContext, setAdditionalContext] = useState('')
  const [includeCompetitors, setIncludeCompetitors] = useState(true)
  const [timePeriod, setTimePeriod] = useState(30)

  const mutation = useMutation({
    mutationFn: startResearch,
    onSuccess: (data) => {
      onResearchStart(data)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!companyName.trim()) return

    mutation.mutate({
      company_name: companyName.trim(),
      ticker_symbol: tickerSymbol.trim() || undefined,
      research_type: researchType,
      additional_context: additionalContext.trim() || undefined,
      include_competitors: includeCompetitors,
      time_period_days: timePeriod,
    })
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            Start New Research
          </CardTitle>
          <CardDescription>
            Enter a company name to generate a comprehensive AI-powered research report
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Company Name */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-white flex items-center gap-2">
                <Building2 className="w-4 h-4" />
                Company Name *
              </label>
              <Input
                placeholder="e.g., Apple, Microsoft, Tesla"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                required
              />
            </div>

            {/* Ticker Symbol */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-white">
                Ticker Symbol (optional)
              </label>
              <Input
                placeholder="e.g., AAPL, MSFT, TSLA"
                value={tickerSymbol}
                onChange={(e) => setTickerSymbol(e.target.value.toUpperCase())}
                maxLength={10}
              />
              <p className="text-xs text-muted-foreground">
                Leave empty to auto-detect
              </p>
            </div>

            {/* Research Type */}
            <div className="space-y-3">
              <label className="text-sm font-medium text-white">
                Research Type
              </label>
              <div className="grid grid-cols-2 gap-3">
                {RESEARCH_TYPE_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setResearchType(option.value as ResearchType)}
                    className={`p-4 rounded-lg border text-left transition-all duration-200 ${
                      researchType === option.value
                        ? 'border-primary bg-primary/10 text-white'
                        : 'border-white/10 bg-white/5 text-muted-foreground hover:border-white/20'
                    }`}
                  >
                    <p className="font-medium text-sm">{option.label}</p>
                    <p className="text-xs mt-1 opacity-80">{option.description}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Time Period */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-white flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                Analysis Period
              </label>
              <select
                value={timePeriod}
                onChange={(e) => setTimePeriod(Number(e.target.value))}
                className="flex h-11 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/50"
              >
                <option value={7}>Last 7 days</option>
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
                <option value={180}>Last 6 months</option>
                <option value={365}>Last year</option>
              </select>
            </div>

            {/* Include Competitors */}
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="competitors"
                checked={includeCompetitors}
                onChange={(e) => setIncludeCompetitors(e.target.checked)}
                className="w-4 h-4 rounded border-white/20 bg-white/5 text-primary focus:ring-primary/50"
              />
              <label htmlFor="competitors" className="text-sm text-white flex items-center gap-2">
                <Users className="w-4 h-4" />
                Include competitor analysis
              </label>
            </div>

            {/* Additional Context */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-white">
                Additional Context (optional)
              </label>
              <textarea
                placeholder="Any specific questions or areas of focus..."
                value={additionalContext}
                onChange={(e) => setAdditionalContext(e.target.value)}
                maxLength={1000}
                rows={3}
                className="flex w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
              />
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              size="lg"
              className="w-full"
              disabled={!companyName.trim() || mutation.isPending}
            >
              {mutation.isPending ? (
                <>
                  <span className="animate-spin mr-2">⏳</span>
                  Starting Research...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5 mr-2" />
                  Start Research
                </>
              )}
            </Button>

            {mutation.isError && (
              <p className="text-sm text-red-400 text-center">
                Failed to start research. Please try again.
              </p>
            )}
          </form>
        </CardContent>
      </Card>
    </motion.div>
  )
}
