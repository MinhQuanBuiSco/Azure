import { useState, useRef } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Send, Loader2, Info, Zap } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, Button, Select, Badge } from '../components/ui'
import { chatCompletionStream, previewRouting, type Message, type RoutingDecision } from '../lib/api'

export default function Playground() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [forceTier, setForceTier] = useState<string>('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [showPreview, setShowPreview] = useState(false)
  const [routingPreview, setRoutingPreview] = useState<{
    decision: RoutingDecision
    complexity_breakdown: Record<string, number>
    alternative_options: Array<{ model: string; tier: string; estimated_cost: number }>
  } | null>(null)
  const [lastRouting, setLastRouting] = useState<RoutingDecision | null>(null)
  const streamingContentRef = useRef('')

  const chatMutation = useMutation({
    mutationFn: async (userMessage: string) => {
      const newMessages: Message[] = [
        ...messages,
        { role: 'user' as const, content: userMessage },
      ]

      setMessages(newMessages)
      setIsStreaming(true)
      setStreamingContent('')
      streamingContentRef.current = ''

      const response = await chatCompletionStream(
        {
          messages: newMessages,
          routing_options: forceTier ? { force_tier: forceTier as 'frontier' | 'standard' | 'fast' } : undefined,
        },
        {
          onChunk: (content) => {
            streamingContentRef.current += content
            setStreamingContent(streamingContentRef.current)
          },
          onRouting: (routing) => {
            setLastRouting(routing)
          },
        }
      )

      return {
        messages: newMessages,
        response,
      }
    },
    onSuccess: ({ messages: newMessages, response }) => {
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.choices[0]?.message?.content || '',
      }
      setMessages([...newMessages, assistantMessage])
      setIsStreaming(false)
      setStreamingContent('')
      streamingContentRef.current = ''
      setRoutingPreview(null)
      if (response.routing) setLastRouting(response.routing)
    },
    onError: () => {
      setIsStreaming(false)
      setStreamingContent('')
      streamingContentRef.current = ''
    },
  })

  const previewMutation = useMutation({
    mutationFn: async (userMessage: string) => {
      const newMessages: Message[] = [
        ...messages,
        { role: 'user' as const, content: userMessage },
      ]

      return previewRouting(
        newMessages,
        forceTier ? { force_tier: forceTier as 'frontier' | 'standard' | 'fast' } : undefined
      )
    },
    onSuccess: (preview) => {
      setRoutingPreview(preview)
      setShowPreview(true)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || chatMutation.isPending || isStreaming) return

    chatMutation.mutate(input)
    setInput('')
  }

  const handlePreview = () => {
    if (!input.trim() || previewMutation.isPending) return
    previewMutation.mutate(input)
  }

  return (
    <div className="flex h-screen flex-col p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Playground</h1>
        <p className="text-gray-600">
          Test the routing system with different queries
        </p>
      </div>

      <div className="flex flex-1 gap-6 overflow-hidden">
        {/* Chat Area */}
        <div className="flex flex-1 flex-col">
          <Card className="flex flex-1 flex-col overflow-hidden">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6">
              {messages.length === 0 ? (
                <div className="flex h-full items-center justify-center text-gray-500">
                  <div className="text-center">
                    <Zap className="mx-auto mb-4 h-12 w-12 text-gray-300" />
                    <p>Start a conversation to test the routing system</p>
                    <p className="mt-1 text-sm">
                      Try different query types to see how they are routed
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((msg, i) => (
                    <div
                      key={i}
                      className={`flex ${
                        msg.role === 'user' ? 'justify-end' : 'justify-start'
                      }`}
                    >
                      <div
                        className={`max-w-[80%] rounded-lg px-4 py-2 ${
                          msg.role === 'user'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-900'
                        }`}
                      >
                        <pre className="whitespace-pre-wrap font-sans">
                          {msg.content}
                        </pre>
                      </div>
                    </div>
                  ))}
                  {isStreaming && streamingContent && (
                    <div className="flex justify-start">
                      <div className="max-w-[80%] rounded-lg bg-gray-100 px-4 py-2 text-gray-900">
                        <pre className="whitespace-pre-wrap font-sans">
                          {streamingContent}
                          <span className="inline-block h-4 w-1 animate-pulse bg-gray-400 align-middle" />
                        </pre>
                      </div>
                    </div>
                  )}
                  {chatMutation.isPending && !streamingContent && (
                    <div className="flex justify-start">
                      <div className="rounded-lg bg-gray-100 px-4 py-2">
                        <Loader2 className="h-5 w-5 animate-spin text-gray-500" />
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Input */}
            <div className="border-t border-gray-200 p-4">
              <form onSubmit={handleSubmit} className="flex gap-3">
                <Select
                  value={forceTier}
                  onChange={(e) => setForceTier(e.target.value)}
                  className="w-40"
                >
                  <option value="">Auto Route</option>
                  <option value="frontier">Frontier</option>
                  <option value="standard">Standard</option>
                  <option value="fast">Fast</option>
                </Select>
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Type your message..."
                  className="flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={handlePreview}
                  disabled={!input.trim() || previewMutation.isPending}
                >
                  {previewMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Info className="h-4 w-4" />
                  )}
                </Button>
                <Button
                  type="submit"
                  disabled={!input.trim() || chatMutation.isPending || isStreaming}
                >
                  {chatMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </form>
            </div>
          </Card>
        </div>

        {/* Routing Info Panel */}
        <div className="w-80 space-y-4">
          {/* Last Routing Decision */}
          {lastRouting && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Last Routing Decision</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Model</span>
                  <span className="font-medium">{lastRouting.selected_model}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Tier</span>
                  <Badge
                    variant={
                      lastRouting.selected_tier === 'frontier'
                        ? 'danger'
                        : lastRouting.selected_tier === 'standard'
                        ? 'info'
                        : 'success'
                    }
                  >
                    {lastRouting.selected_tier}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Complexity</span>
                  <span className="font-medium">{lastRouting.complexity_score}/100</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Category</span>
                  <span className="font-medium">{lastRouting.query_category}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Cost</span>
                  <span className="font-medium">
                    ${lastRouting.estimated_cost.toFixed(6)}
                  </span>
                </div>
                <div className="border-t border-gray-200 pt-3">
                  <span className="text-sm text-gray-600">Reason</span>
                  <p className="mt-1 text-sm text-gray-900">
                    {lastRouting.routing_reason}
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Routing Preview */}
          {showPreview && routingPreview && (
            <Card className="border-blue-200">
              <CardHeader className="bg-blue-50">
                <CardTitle className="text-base text-blue-900">
                  Routing Preview
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Would Route To</span>
                  <Badge
                    variant={
                      routingPreview.decision.selected_tier === 'frontier'
                        ? 'danger'
                        : routingPreview.decision.selected_tier === 'standard'
                        ? 'info'
                        : 'success'
                    }
                  >
                    {routingPreview.decision.selected_model}
                  </Badge>
                </div>

                <div>
                  <span className="text-sm text-gray-600">Complexity Breakdown</span>
                  <div className="mt-2 space-y-1">
                    {Object.entries(routingPreview.complexity_breakdown).map(
                      ([key, value]) => (
                        <div
                          key={key}
                          className="flex items-center justify-between text-xs"
                        >
                          <span className="text-gray-500">
                            {key.replace(/_/g, ' ')}
                          </span>
                          <span className="font-medium">{value.toFixed(1)}</span>
                        </div>
                      )
                    )}
                  </div>
                </div>

                <div>
                  <span className="text-sm text-gray-600">Alternatives</span>
                  <div className="mt-2 space-y-1">
                    {routingPreview.alternative_options.map((opt, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between rounded bg-gray-50 px-2 py-1 text-xs"
                      >
                        <span>
                          {opt.tier}: {opt.model}
                        </span>
                        <span>${opt.estimated_cost.toFixed(6)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full"
                  onClick={() => setShowPreview(false)}
                >
                  Dismiss
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Query Examples */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Try These Examples</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <ExampleButton
                  label="Simple Chat"
                  example="Hello, how are you today?"
                  tier="fast"
                  onClick={() => setInput('Hello, how are you today?')}
                />
                <ExampleButton
                  label="Coding"
                  example="Write a Python function to sort a list"
                  tier="standard"
                  onClick={() =>
                    setInput('Write a Python function to sort a list of numbers')
                  }
                />
                <ExampleButton
                  label="Complex Reasoning"
                  example="Explain quantum entanglement implications"
                  tier="frontier"
                  onClick={() =>
                    setInput(
                      'Explain the implications of quantum entanglement for quantum computing and how it differs from classical computing paradigms'
                    )
                  }
                />
                <ExampleButton
                  label="Math"
                  example="Solve differential equation"
                  tier="frontier"
                  onClick={() =>
                    setInput(
                      'Solve the differential equation dy/dx = 3x^2 + 2x with initial condition y(0) = 1'
                    )
                  }
                />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

interface ExampleButtonProps {
  label: string
  example: string
  tier: string
  onClick: () => void
}

function ExampleButton({ label, example, tier, onClick }: ExampleButtonProps) {
  return (
    <button
      onClick={onClick}
      className="w-full rounded-lg border border-gray-200 p-2 text-left transition-colors hover:bg-gray-50"
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-900">{label}</span>
        <Badge
          variant={
            tier === 'frontier'
              ? 'danger'
              : tier === 'standard'
              ? 'info'
              : 'success'
          }
        >
          {tier}
        </Badge>
      </div>
      <p className="mt-1 truncate text-xs text-gray-500">{example}</p>
    </button>
  )
}
