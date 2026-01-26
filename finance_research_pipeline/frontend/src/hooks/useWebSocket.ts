import { useCallback, useEffect, useRef, useState } from 'react'
import type { WebSocketMessage, AgentProgress, PipelineProgress } from '../types/research'

interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void
  onAgentProgress?: (progress: AgentProgress) => void
  onPipelineProgress?: (progress: PipelineProgress) => void
  onComplete?: (summary?: string) => void
  onError?: (error: string) => void
  autoReconnect?: boolean
}

interface UseWebSocketReturn {
  isConnected: boolean
  connect: () => void
  disconnect: () => void
  sendPing: () => void
}

export function useWebSocket(
  researchId: string | null,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const {
    onMessage,
    onAgentProgress,
    onPipelineProgress,
    onComplete,
    onError,
    autoReconnect = true,
  } = options

  const connect = useCallback(() => {
    if (!researchId || wsRef.current?.readyState === WebSocket.OPEN) return

    // Construct WebSocket URL
    let wsUrl: string
    if (import.meta.env.VITE_WS_URL) {
      // Local development with explicit WS URL
      wsUrl = `${import.meta.env.VITE_WS_URL}/api/v1/ws/research/${researchId}`
    } else {
      // Production: use relative URL through nginx proxy
      // nginx maps /ws/ to backend's /api/v1/ws/
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      wsUrl = `${protocol}//${window.location.host}/ws/research/${researchId}`
    }

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket connected:', researchId)
        setIsConnected(true)
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          onMessage?.(message)

          switch (message.type) {
            case 'agent_progress':
              // Backend sends { agent_type: string, progress: AgentProgress }
              // Extract the actual progress object
              const agentPayload = message.payload as { agent_type: string; progress: AgentProgress }
              if (agentPayload.progress) {
                onAgentProgress?.(agentPayload.progress)
              }
              break
            case 'pipeline_progress':
              onPipelineProgress?.(message.payload as unknown as PipelineProgress)
              break
            case 'complete':
              onComplete?.(message.payload.summary as string | undefined)
              break
            case 'error':
              onError?.(message.payload.error as string)
              break
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        onError?.('WebSocket connection error')
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected:', researchId)
        setIsConnected(false)

        // Auto-reconnect if enabled
        if (autoReconnect && researchId) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, 3000)
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      onError?.('Failed to establish WebSocket connection')
    }
  }, [researchId, autoReconnect, onMessage, onAgentProgress, onPipelineProgress, onComplete, onError])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setIsConnected(false)
  }, [])

  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'ping' }))
    }
  }, [])

  // Connect when researchId changes
  useEffect(() => {
    if (researchId) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [researchId, connect, disconnect])

  // Ping interval to keep connection alive
  useEffect(() => {
    if (!isConnected) return

    const pingInterval = setInterval(() => {
      sendPing()
    }, 30000)

    return () => clearInterval(pingInterval)
  }, [isConnected, sendPing])

  return {
    isConnected,
    connect,
    disconnect,
    sendPing,
  }
}
