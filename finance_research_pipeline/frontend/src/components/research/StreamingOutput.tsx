import { useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { FileText, Download } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import type { ResearchResult } from '../../types/research'

interface StreamingOutputProps {
  researchId: string
  result?: ResearchResult | null
  streamingContent?: string
  isComplete: boolean
}

export default function StreamingOutput({
  researchId,
  result,
  streamingContent,
  isComplete,
}: StreamingOutputProps) {
  const contentRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new content arrives
  useEffect(() => {
    if (contentRef.current && streamingContent) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight
    }
  }, [streamingContent])

  const handleDownloadPDF = async () => {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || ''}/api/v1/research/${researchId}/report/pdf`
      )

      if (!response.ok) throw new Error('Failed to download PDF')

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `research_report_${researchId.slice(0, 8)}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Failed to download PDF:', error)
    }
  }

  const content = result?.full_report || streamingContent || ''

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="flex items-center gap-3">
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-primary" />
            Research Report
          </CardTitle>
          {isComplete && (
            <Badge variant="success">Complete</Badge>
          )}
          {!isComplete && streamingContent && (
            <Badge variant="default" className="animate-pulse">
              Generating...
            </Badge>
          )}
        </div>
        {isComplete && (
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleDownloadPDF}>
              <Download className="w-4 h-4 mr-2" />
              Download PDF
            </Button>
          </div>
        )}
      </CardHeader>
      <CardContent>
        {/* Executive Summary */}
        {result?.executive_summary && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 rounded-lg bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20"
          >
            <h3 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-blue-500" />
              Executive Summary
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {result.executive_summary}
            </p>
          </motion.div>
        )}

        {/* Recommendations */}
        {result?.recommendations && result.recommendations.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mb-6"
          >
            <h3 className="text-sm font-semibold text-white mb-3">Key Recommendations</h3>
            <ul className="space-y-2">
              {result.recommendations.map((rec, index) => (
                <li
                  key={index}
                  className="flex items-start gap-3 p-3 rounded-lg bg-green-500/10 border border-green-500/20"
                >
                  <span className="w-6 h-6 rounded-full bg-green-500/20 text-green-400 flex items-center justify-center text-xs font-bold flex-shrink-0">
                    {index + 1}
                  </span>
                  <span className="text-sm text-muted-foreground">{rec}</span>
                </li>
              ))}
            </ul>
          </motion.div>
        )}

        {/* Full Report Content */}
        {content && (
          <div
            ref={contentRef}
            className="prose prose-invert prose-sm max-w-none max-h-[600px] overflow-y-auto pr-4"
            style={{
              scrollbarWidth: 'thin',
              scrollbarColor: 'rgba(255,255,255,0.1) transparent',
            }}
          >
            <div className="whitespace-pre-wrap text-sm text-muted-foreground leading-relaxed">
              {content}
              {!isComplete && (
                <motion.span
                  animate={{ opacity: [1, 0, 1] }}
                  transition={{ duration: 1, repeat: Infinity }}
                  className="inline-block w-2 h-4 bg-primary ml-1"
                />
              )}
            </div>
          </div>
        )}

        {!content && !isComplete && (
          <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <div className="w-12 h-12 rounded-full border-2 border-primary/30 border-t-primary animate-spin mb-4" />
            <p className="text-sm">Waiting for report generation...</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
