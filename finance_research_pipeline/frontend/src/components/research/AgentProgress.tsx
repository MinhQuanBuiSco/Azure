import { motion } from 'framer-motion'
import { Progress } from '../ui/progress'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import AgentCard from './AgentCard'
import type { AgentProgress as AgentProgressType, AgentType } from '../../types/research'
import { AGENT_CONFIG } from '../../types/research'

interface AgentProgressProps {
  progress: Record<string, AgentProgressType>
  overallProgress: number
  currentAgent?: AgentType | null
  isComplete?: boolean
}

const AGENT_ORDER: AgentType[] = [
  'supervisor',
  'web_research',
  'financial_data',
  'news_analysis',
  'analyst',
  'writer',
  'reviewer',
]

export default function AgentProgress({
  progress,
  overallProgress,
  currentAgent,
  isComplete = false,
}: AgentProgressProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Research Progress</span>
          <span className="text-primary">{Math.round(overallProgress)}%</span>
        </CardTitle>
        <Progress value={overallProgress} className="mt-3" />
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {AGENT_ORDER.map((agentType, index) => {
            const agentProgress = progress[agentType]
            const config = AGENT_CONFIG[agentType]
            const isActive = currentAgent === agentType

            // If research is complete, show all agents as completed
            const status = isComplete
              ? 'completed'
              : (agentProgress?.status || 'idle')
            const agentProgressValue = isComplete
              ? 100
              : (agentProgress?.progress || 0)
            const message = isComplete
              ? 'Completed'
              : agentProgress?.message

            return (
              <motion.div
                key={agentType}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                <AgentCard
                  agentType={agentType}
                  label={config.label}
                  icon={config.icon}
                  color={config.color}
                  status={status}
                  progress={agentProgressValue}
                  message={message}
                  isActive={isActive}
                />
              </motion.div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
