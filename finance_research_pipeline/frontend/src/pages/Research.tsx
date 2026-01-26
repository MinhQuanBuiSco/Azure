import { useState, useCallback, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import ResearchForm from '../components/research/ResearchForm'
import AgentProgress from '../components/research/AgentProgress'
import StreamingOutput from '../components/research/StreamingOutput'
import { useWebSocket } from '../hooks/useWebSocket'
import type { ResearchResponse, ResearchResult, AgentProgress as AgentProgressType, AgentType } from '../types/research'

async function fetchResearchStatus(researchId: string): Promise<ResearchResponse> {
  const response = await fetch(
    `${import.meta.env.VITE_API_URL || ''}/api/v1/research/${researchId}`
  )
  if (!response.ok) throw new Error('Failed to fetch research status')
  return response.json()
}

async function fetchResearchResult(researchId: string): Promise<ResearchResult> {
  const response = await fetch(
    `${import.meta.env.VITE_API_URL || ''}/api/v1/research/${researchId}/result`
  )
  if (!response.ok) throw new Error('Failed to fetch research result')
  return response.json()
}

export default function Research() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [researchId, setResearchId] = useState<string | null>(id || null)
  const [agentProgress, setAgentProgress] = useState<Record<string, AgentProgressType>>({})
  const [overallProgress, setOverallProgress] = useState(0)
  const [currentAgent, setCurrentAgent] = useState<AgentType | null>(null)
  const [isComplete, setIsComplete] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')

  // Fetch research status
  const { data: status } = useQuery({
    queryKey: ['research-status', researchId],
    queryFn: () => fetchResearchStatus(researchId!),
    enabled: !!researchId && !isComplete,
    refetchInterval: isComplete ? false : 5000,
  })

  // Fetch result when complete
  const { data: result } = useQuery({
    queryKey: ['research-result', researchId],
    queryFn: () => fetchResearchResult(researchId!),
    enabled: !!researchId && isComplete,
  })

  // WebSocket for real-time updates
  const handleAgentProgress = useCallback((progress: AgentProgressType) => {
    setAgentProgress((prev) => ({
      ...prev,
      [progress.agent_type]: progress,
    }))
  }, [])

  const handleWebSocketMessage = useCallback((message: any) => {
    if (message.type === 'progress_update') {
      setOverallProgress(message.payload.overall_progress || 0)
      if (message.payload.current_agent) {
        setCurrentAgent(message.payload.current_agent as AgentType)
      }
    }
  }, [])

  const handleComplete = useCallback(() => {
    setIsComplete(true)
    setOverallProgress(100)
  }, [])

  const handleError = useCallback((error: string) => {
    console.error('Research error:', error)
  }, [])

  useWebSocket(researchId, {
    onMessage: handleWebSocketMessage,
    onAgentProgress: handleAgentProgress,
    onComplete: handleComplete,
    onError: handleError,
  })

  // Also check status from REST API in case WebSocket messages were missed
  useEffect(() => {
    if (status) {
      // Update progress from REST API
      if (status.progress !== undefined && status.progress > 0) {
        setOverallProgress(status.progress)
      }
      // Check for completion
      if (status.status === 'completed' || status.status === 'failed') {
        setIsComplete(true)
        if (status.progress === undefined || status.progress === 0) {
          setOverallProgress(100)
        }
      }
    }
  }, [status])

  // Handle research start
  const handleResearchStart = (response: ResearchResponse) => {
    setResearchId(response.research_id)
    setIsComplete(false)
    setAgentProgress({})
    setOverallProgress(0)
    setStreamingContent('')
    navigate(`/research/${response.research_id}`, { replace: true })
  }

  return (
    <div className="py-8 space-y-8">
      <AnimatePresence mode="wait">
        {!researchId ? (
          <motion.div
            key="form"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <ResearchForm onResearchStart={handleResearchStart} />
          </motion.div>
        ) : (
          <motion.div
            key="progress"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-8"
          >
            {/* Header with company info */}
            {status && (
              <div className="glass-card p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h1 className="text-2xl font-bold text-white mb-1">
                      {status.company_name}
                    </h1>
                    <p className="text-muted-foreground">
                      {status.ticker_symbol && (
                        <span className="text-primary font-mono mr-3">
                          {status.ticker_symbol}
                        </span>
                      )}
                      Research ID: {researchId.slice(0, 8)}...
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Status</p>
                    <p className={`font-semibold ${
                      status.status === 'completed' ? 'text-green-400' :
                      status.status === 'failed' ? 'text-red-400' :
                      'text-primary'
                    }`}>
                      {status.status.replace('_', ' ').toUpperCase()}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Agent Progress */}
            <AgentProgress
              progress={agentProgress}
              overallProgress={overallProgress}
              currentAgent={currentAgent}
              isComplete={isComplete}
            />

            {/* Streaming Output / Report */}
            <StreamingOutput
              researchId={researchId}
              result={result}
              streamingContent={streamingContent}
              isComplete={isComplete}
            />

            {/* Start New Research Button */}
            {isComplete && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center"
              >
                <button
                  onClick={() => {
                    setResearchId(null)
                    navigate('/research', { replace: true })
                  }}
                  className="text-primary hover:underline"
                >
                  Start New Research
                </button>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
