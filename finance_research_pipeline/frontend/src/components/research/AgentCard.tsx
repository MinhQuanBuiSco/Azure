import { motion } from 'framer-motion'
import { Check, Loader2, AlertCircle, Clock, SkipForward } from 'lucide-react'
import { Progress } from '../ui/progress'
import { Badge } from '../ui/badge'
import type { AgentStatus, AgentType } from '../../types/research'

interface AgentCardProps {
  agentType: AgentType
  label: string
  icon: string
  color: string
  status: AgentStatus
  progress: number
  message?: string
  isActive?: boolean
}

const STATUS_CONFIG: Record<AgentStatus, { icon: typeof Check; label: string; variant: 'default' | 'success' | 'warning' | 'error' | 'secondary' }> = {
  idle: { icon: Clock, label: 'Waiting', variant: 'secondary' },
  running: { icon: Loader2, label: 'Running', variant: 'default' },
  completed: { icon: Check, label: 'Complete', variant: 'success' },
  error: { icon: AlertCircle, label: 'Error', variant: 'error' },
  skipped: { icon: SkipForward, label: 'Skipped', variant: 'warning' },
}

export default function AgentCard({
  agentType,
  label,
  icon,
  color,
  status,
  progress,
  message,
  isActive,
}: AgentCardProps) {
  const statusConfig = STATUS_CONFIG[status]
  const StatusIcon = statusConfig.icon

  return (
    <div
      className={`glass-card p-4 transition-all duration-300 ${
        isActive ? 'glow border-primary/50' : ''
      } ${status === 'completed' ? 'border-green-500/30' : ''} ${
        status === 'error' ? 'border-red-500/30' : ''
      }`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div
            className={`relative w-10 h-10 rounded-xl flex items-center justify-center text-xl ${
              isActive ? 'agent-active' : ''
            }`}
            style={{
              background: `linear-gradient(135deg, var(--tw-gradient-from), var(--tw-gradient-to))`,
              '--tw-gradient-from': `rgb(var(--${color}-500) / 0.2)`,
              '--tw-gradient-to': `rgb(var(--${color}-600) / 0.1)`,
            } as React.CSSProperties}
          >
            {icon}
          </div>
          <div>
            <p className="font-medium text-white text-sm">{label}</p>
            <p className="text-xs text-muted-foreground">{agentType}</p>
          </div>
        </div>
        <Badge variant={statusConfig.variant} className="flex items-center gap-1">
          <StatusIcon
            className={`w-3 h-3 ${status === 'running' ? 'animate-spin' : ''}`}
          />
          {statusConfig.label}
        </Badge>
      </div>

      {status !== 'idle' && status !== 'skipped' && (
        <div className="space-y-2">
          <Progress value={progress} className="h-1.5" />
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground truncate max-w-[70%]">
              {message || 'Processing...'}
            </span>
            <span className="text-primary font-medium">{Math.round(progress)}%</span>
          </div>
        </div>
      )}

      {status === 'idle' && (
        <p className="text-xs text-muted-foreground">Waiting to start...</p>
      )}

      {status === 'skipped' && (
        <p className="text-xs text-muted-foreground">Skipped based on research type</p>
      )}

      {isActive && status === 'running' && (
        <motion.div
          className="mt-3 h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full"
          animate={{
            backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'linear',
          }}
          style={{
            backgroundSize: '200% 200%',
          }}
        />
      )}
    </div>
  )
}
