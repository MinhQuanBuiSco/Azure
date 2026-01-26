import { useCallback, useEffect, useRef, useState } from 'react'

interface UseSSEOptions {
  onToken?: (token: string, agent: string) => void
  onAgentUpdate?: (agent: string, status: string) => void
  onComplete?: () => void
  onError?: (error: string) => void
  onProgress?: (progress: number) => void
}

interface UseSSEReturn {
  isConnected: boolean
  connect: () => void
  disconnect: () => void
}

export function useSSE(
  researchId: string | null,
  options: UseSSEOptions = {}
): UseSSEReturn {
  const [isConnected, setIsConnected] = useState(false)
  const eventSourceRef = useRef<EventSource | null>(null)

  const { onToken, onAgentUpdate, onComplete, onError, onProgress } = options

  const connect = useCallback(() => {
    if (!researchId || eventSourceRef.current) return

    // Use relative URL in production (goes through nginx proxy)
    // Use VITE_API_URL only for local development
    const sseUrl = import.meta.env.VITE_API_URL
      ? `${import.meta.env.VITE_API_URL}/api/v1/sse/research/${researchId}/stream`
      : `/api/v1/sse/research/${researchId}/stream`

    try {
      const eventSource = new EventSource(sseUrl)
      eventSourceRef.current = eventSource

      eventSource.onopen = () => {
        console.log('SSE connected:', researchId)
        setIsConnected(true)
      }

      eventSource.addEventListener('connected', (event) => {
        console.log('SSE connected event:', event.data)
      })

      eventSource.addEventListener('token', (event) => {
        try {
          const data = JSON.parse(event.data)
          onToken?.(data.token, data.agent)
        } catch (e) {
          console.error('Failed to parse token event:', e)
        }
      })

      eventSource.addEventListener('agent_update', (event) => {
        try {
          const data = JSON.parse(event.data)
          onAgentUpdate?.(data.agent, data.status)
        } catch (e) {
          console.error('Failed to parse agent_update event:', e)
        }
      })

      eventSource.addEventListener('progress', (event) => {
        try {
          const data = JSON.parse(event.data)
          onProgress?.(data.progress)
        } catch (e) {
          console.error('Failed to parse progress event:', e)
        }
      })

      eventSource.addEventListener('complete', () => {
        console.log('SSE complete event')
        onComplete?.()
        disconnect()
      })

      eventSource.addEventListener('error', (event: Event) => {
        try {
          const messageEvent = event as MessageEvent
          if (messageEvent.data) {
            const data = JSON.parse(messageEvent.data)
            onError?.(data.error)
          }
        } catch (e) {
          console.error('SSE error:', e)
          onError?.('SSE connection error')
        }
        disconnect()
      })

      eventSource.onerror = (error) => {
        console.error('SSE connection error:', error)
        setIsConnected(false)
        onError?.('SSE connection lost')
      }
    } catch (error) {
      console.error('Failed to create SSE connection:', error)
      onError?.('Failed to establish SSE connection')
    }
  }, [researchId, onToken, onAgentUpdate, onComplete, onError, onProgress])

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setIsConnected(false)
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

  return {
    isConnected,
    connect,
    disconnect,
  }
}
