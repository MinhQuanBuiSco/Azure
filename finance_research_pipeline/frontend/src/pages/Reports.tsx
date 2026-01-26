import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FileText, Calendar, Building2, TrendingUp, Download, ExternalLink } from 'lucide-react'
import { Card, CardContent } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import type { ReportListResponse, ResearchStatus } from '../types/research'

async function fetchReports(page: number = 1): Promise<ReportListResponse> {
  const response = await fetch(
    `${import.meta.env.VITE_API_URL || ''}/api/v1/research/?page=${page}&page_size=20`
  )
  if (!response.ok) throw new Error('Failed to fetch reports')
  return response.json()
}

const STATUS_VARIANT: Record<ResearchStatus, 'default' | 'success' | 'warning' | 'error' | 'secondary'> = {
  pending: 'secondary',
  in_progress: 'default',
  completed: 'success',
  failed: 'error',
  cancelled: 'warning',
}

export default function Reports() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['reports'],
    queryFn: () => fetchReports(),
  })

  const handleDownloadPDF = async (researchId: string, companyName: string) => {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || ''}/api/v1/research/${researchId}/report/pdf`
      )

      if (!response.ok) throw new Error('Failed to download PDF')

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `research_report_${companyName.replace(/\s+/g, '_')}_${researchId.slice(0, 8)}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Failed to download PDF:', error)
    }
  }

  return (
    <div className="py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-white mb-2">Research Reports</h1>
        <p className="text-muted-foreground">
          View and download your generated research reports
        </p>
      </motion.div>

      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="w-12 h-12 rounded-full border-2 border-primary/30 border-t-primary animate-spin" />
        </div>
      )}

      {error && (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-red-400">Failed to load reports. Please try again.</p>
          </CardContent>
        </Card>
      )}

      {data && data.reports.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">No Reports Yet</h3>
            <p className="text-muted-foreground mb-4">
              Start your first research to generate a report
            </p>
            <Button asChild>
              <Link to="/research">Start Research</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {data && data.reports.length > 0 && (
        <div className="space-y-4">
          {data.reports.map((report, index) => (
            <motion.div
              key={report.research_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <Card className="hover:border-white/20 transition-all duration-300">
                <CardContent className="py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center">
                        <Building2 className="w-6 h-6 text-primary" />
                      </div>
                      <div>
                        <div className="flex items-center gap-3">
                          <h3 className="font-semibold text-white">
                            {report.company_name}
                          </h3>
                          {report.ticker_symbol && (
                            <span className="text-sm font-mono text-primary">
                              {report.ticker_symbol}
                            </span>
                          )}
                          <Badge variant={STATUS_VARIANT[report.status]}>
                            {report.status.replace('_', ' ')}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            {new Date(report.created_at).toLocaleDateString()}
                          </span>
                          <span className="flex items-center gap-1">
                            <TrendingUp className="w-4 h-4" />
                            {report.research_type.replace('_', ' ')}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {report.status === 'completed' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDownloadPDF(report.research_id, report.company_name)}
                        >
                          <Download className="w-4 h-4 mr-2" />
                          PDF
                        </Button>
                      )}
                      <Button variant="ghost" size="sm" asChild>
                        <Link to={`/research/${report.research_id}`}>
                          <ExternalLink className="w-4 h-4 mr-2" />
                          View
                        </Link>
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}

          {/* Pagination info */}
          <div className="text-center text-sm text-muted-foreground pt-4">
            Showing {data.reports.length} of {data.total} reports
          </div>
        </div>
      )}
    </div>
  )
}
