import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Bot,
  Send,
  Plane,
  Hotel,
  Sun,
  MapPin,
  DollarSign,
  Star,
  Clock,
  Calendar,
  Users,
  Sparkles,
  User,
  Loader2,
} from 'lucide-react'
import {
  processAIAgentQuery,
  type AIAgentResponse,
  type ConversationMessage,
  type CollectedParams,
  type TripPlanResponse,
} from '../services/api'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.12,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 24 },
  show: {
    opacity: 1,
    y: 0,
    transition: {
      type: 'spring',
      stiffness: 100,
      damping: 15,
    },
  },
}

const messageVariants = {
  hidden: { opacity: 0, y: 10, scale: 0.95 },
  show: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      type: 'spring',
      stiffness: 200,
      damping: 20,
    },
  },
}

const INITIAL_MESSAGE = "Hi! I'm your AI travel assistant. Tell me about the trip you're dreaming of, and I'll help you plan it step by step. Where would you like to go?"

export default function AIAgent() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '0',
      role: 'assistant',
      content: INITIAL_MESSAGE,
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [collectedParams, setCollectedParams] = useState<CollectedParams>({})
  const [results, setResults] = useState<TripPlanResponse | null>(null)
  const [showResults, setShowResults] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Build conversation history for API
  const getConversationHistory = (): ConversationMessage[] => {
    return messages.slice(1).map((msg) => ({
      role: msg.role,
      content: msg.content,
    }))
  }

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response: AIAgentResponse = await processAIAgentQuery({
        query: userMessage.content,
        conversation_history: getConversationHistory(),
        collected_params: collectedParams,
      })

      // Update collected params
      setCollectedParams(response.collected_params)

      // Add AI response
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])

      // If complete, show results
      if (response.is_complete && response.trip_plan) {
        setResults(response.trip_plan)
        setTimeout(() => setShowResults(true), 1000)
      }
    } catch (error) {
      console.error('AI Agent error:', error)
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I'm sorry, something went wrong. Could you try again?",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const resetConversation = () => {
    setMessages([
      {
        id: '0',
        role: 'assistant',
        content: INITIAL_MESSAGE,
        timestamp: new Date(),
      },
    ])
    setCollectedParams({})
    setResults(null)
    setShowResults(false)
  }

  // Count collected params
  const paramCount = Object.values(collectedParams).filter(
    (v) => v !== null && v !== undefined && v !== ''
  ).length

  return (
    <div className="w-full max-w-4xl mx-auto flex flex-col h-[calc(100vh-12rem)]">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-6"
      >
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-card border border-border mb-4">
          <Bot className="w-4 h-4 text-accent" />
          <span className="text-sm font-medium text-muted">AI Travel Assistant</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-foreground">
          Plan Your <span className="text-gradient">Perfect Trip</span>
        </h1>
      </motion.div>

      {/* Main Content */}
      <div className="flex-1 flex gap-6 min-h-0">
        {/* Chat Section */}
        <div className="flex-1 flex flex-col glass-card overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            <AnimatePresence>
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  variants={messageVariants}
                  initial="hidden"
                  animate="show"
                  className={`flex gap-3 ${
                    message.role === 'user' ? 'flex-row-reverse' : ''
                  }`}
                >
                  {/* Avatar */}
                  <div
                    className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                      message.role === 'assistant'
                        ? 'bg-gradient-to-br from-accent to-accent-violet'
                        : 'bg-card border border-border'
                    }`}
                  >
                    {message.role === 'assistant' ? (
                      <Bot className="w-4 h-4 text-background" />
                    ) : (
                      <User className="w-4 h-4 text-muted" />
                    )}
                  </div>

                  {/* Message Bubble */}
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                      message.role === 'assistant'
                        ? 'bg-card border border-border rounded-tl-sm'
                        : 'bg-accent/20 border border-accent/30 rounded-tr-sm'
                    }`}
                  >
                    <p className="text-foreground text-sm leading-relaxed whitespace-pre-wrap">
                      {message.content}
                    </p>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Typing indicator */}
            {isLoading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex gap-3"
              >
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent to-accent-violet flex items-center justify-center">
                  <Bot className="w-4 h-4 text-background" />
                </div>
                <div className="bg-card border border-border rounded-2xl rounded-tl-sm px-4 py-3">
                  <div className="typing-indicator">
                    <div className="typing-dot" />
                    <div className="typing-dot" />
                    <div className="typing-dot" />
                  </div>
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-border bg-card/50">
            <div className="flex gap-3">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={showResults ? "Ask follow-up questions..." : "Type your message..."}
                disabled={isLoading}
                className="flex-1 input-field"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className="btn-primary px-4"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Sidebar - Collected Params */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="w-72 hidden lg:block"
        >
          <div className="glass-card p-5 sticky top-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-foreground flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-accent" />
                Trip Details
              </h3>
              {paramCount > 0 && (
                <button
                  onClick={resetConversation}
                  className="text-xs text-muted hover:text-foreground transition-colors"
                >
                  Reset
                </button>
              )}
            </div>

            <div className="space-y-3">
              {/* Destination */}
              <div className={`p-3 rounded-lg border ${collectedParams.destination ? 'bg-accent/10 border-accent/30' : 'bg-card border-border'}`}>
                <div className="flex items-center gap-2 text-xs text-muted mb-1">
                  <MapPin className="w-3 h-3" />
                  Destination
                </div>
                <p className={`text-sm font-medium ${collectedParams.destination ? 'text-foreground' : 'text-subtle'}`}>
                  {collectedParams.destination || 'Not set'}
                </p>
              </div>

              {/* Departure */}
              <div className={`p-3 rounded-lg border ${collectedParams.departure_city ? 'bg-accent/10 border-accent/30' : 'bg-card border-border'}`}>
                <div className="flex items-center gap-2 text-xs text-muted mb-1">
                  <Plane className="w-3 h-3" />
                  From
                </div>
                <p className={`text-sm font-medium ${collectedParams.departure_city ? 'text-foreground' : 'text-subtle'}`}>
                  {collectedParams.departure_city || 'Not set'}
                </p>
              </div>

              {/* Dates */}
              <div className={`p-3 rounded-lg border ${collectedParams.start_date ? 'bg-accent/10 border-accent/30' : 'bg-card border-border'}`}>
                <div className="flex items-center gap-2 text-xs text-muted mb-1">
                  <Calendar className="w-3 h-3" />
                  Dates
                </div>
                <p className={`text-sm font-medium ${collectedParams.start_date ? 'text-foreground' : 'text-subtle'}`}>
                  {collectedParams.start_date && collectedParams.end_date
                    ? `${collectedParams.start_date} → ${collectedParams.end_date}`
                    : 'Not set'}
                </p>
              </div>

              {/* Travelers */}
              <div className={`p-3 rounded-lg border ${collectedParams.travelers ? 'bg-accent/10 border-accent/30' : 'bg-card border-border'}`}>
                <div className="flex items-center gap-2 text-xs text-muted mb-1">
                  <Users className="w-3 h-3" />
                  Travelers
                </div>
                <p className={`text-sm font-medium ${collectedParams.travelers ? 'text-foreground' : 'text-subtle'}`}>
                  {collectedParams.travelers ? `${collectedParams.travelers} people` : 'Not set'}
                </p>
              </div>

              {/* Travel Style */}
              {collectedParams.travel_style && (
                <div className="p-3 rounded-lg border bg-accent-violet/10 border-accent-violet/30">
                  <div className="flex items-center gap-2 text-xs text-muted mb-1">
                    <DollarSign className="w-3 h-3" />
                    Style
                  </div>
                  <p className="text-sm font-medium text-foreground capitalize">
                    {collectedParams.travel_style}
                  </p>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </div>

      {/* Results Section */}
      <AnimatePresence>
        {showResults && results && (
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 40 }}
            transition={{ duration: 0.5 }}
            className="fixed inset-0 z-50 bg-background/95 backdrop-blur-sm overflow-y-auto flex justify-center"
          >
            <div className="w-full max-w-4xl py-8 px-6">
              {/* Close button */}
              <div className="w-full flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-foreground">
                  Your Trip to <span className="text-gradient">{results.destination}</span>
                </h2>
                <button
                  onClick={() => setShowResults(false)}
                  className="btn-secondary"
                >
                  Back to Chat
                </button>
              </div>

              {/* Results Cards */}
              <motion.div
                variants={containerVariants}
                initial="hidden"
                animate="show"
                className="space-y-6"
              >
                {/* Flights */}
                <motion.section variants={itemVariants} className="glass-card glass-card-cyan p-6">
                  <div className="result-header">
                    <div className="result-icon icon-cyan">
                      <Plane className="w-5 h-5 text-white" />
                    </div>
                    <h3 className="text-xl font-semibold text-foreground">Flights</h3>
                  </div>
                  {results.flights?.flights && results.flights.flights.length > 0 ? (
                    <div className="space-y-3">
                      {results.flights.flights.slice(0, 3).map((flight: any, idx: number) => (
                        <div key={idx} className="rounded-xl bg-background/50 border border-border/50 p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                              <div className="text-center">
                                <p className="text-lg font-semibold text-foreground">{flight.departure_time || '--:--'}</p>
                                <p className="text-xs text-muted">{flight.origin || results.departure_city}</p>
                              </div>
                              <div className="flex items-center gap-2 text-muted">
                                <div className="w-8 h-px bg-border"></div>
                                <Plane className="w-4 h-4" />
                                <div className="w-8 h-px bg-border"></div>
                              </div>
                              <div className="text-center">
                                <p className="text-lg font-semibold text-foreground">{flight.arrival_time || '--:--'}</p>
                                <p className="text-xs text-muted">{flight.destination || results.destination}</p>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="text-lg font-bold text-accent-cyan">{flight.price || 'N/A'}</p>
                              <p className="text-xs text-muted">{flight.airline || 'Various Airlines'}</p>
                            </div>
                          </div>
                          {flight.duration && (
                            <div className="flex items-center gap-1 mt-2 text-xs text-subtle">
                              <Clock className="w-3 h-3" />
                              <span>{flight.duration}</span>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted">Flight information not available.</p>
                  )}
                </motion.section>

                {/* Hotels */}
                <motion.section variants={itemVariants} className="glass-card glass-card-violet p-6">
                  <div className="result-header">
                    <div className="result-icon icon-violet">
                      <Hotel className="w-5 h-5 text-white" />
                    </div>
                    <h3 className="text-xl font-semibold text-foreground">Hotels</h3>
                  </div>
                  {results.hotels?.hotels && results.hotels.hotels.length > 0 ? (
                    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                      {results.hotels.hotels.slice(0, 3).map((hotel, idx) => (
                        <div key={idx} className="rounded-xl bg-background/50 border border-border/50 overflow-hidden">
                          {hotel.images && hotel.images[0] && (
                            <div className="h-32 overflow-hidden">
                              <img
                                src={hotel.images[0].thumbnail || hotel.images[0].original_image}
                                alt={hotel.name}
                                className="w-full h-full object-cover"
                                onError={(e) => { e.currentTarget.style.display = 'none' }}
                              />
                            </div>
                          )}
                          <div className="p-4">
                            <p className="font-medium text-foreground mb-2">{hotel.name}</p>
                            <div className="flex items-center gap-2 mb-2">
                              <Star className="w-4 h-4 text-accent-amber fill-current" />
                              <span className="text-sm text-muted">{hotel.rating}</span>
                            </div>
                            <p className="text-lg font-bold text-accent-violet">
                              {hotel.price_per_night}
                              <span className="text-sm font-normal text-subtle">/night</span>
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted">No hotels found.</p>
                  )}
                </motion.section>

                {/* Weather */}
                <motion.section variants={itemVariants} className="glass-card glass-card-amber p-6">
                  <div className="result-header">
                    <div className="result-icon icon-amber">
                      <Sun className="w-5 h-5 text-white" />
                    </div>
                    <h3 className="text-xl font-semibold text-foreground">Weather</h3>
                  </div>
                  {results.weather?.forecast && results.weather.forecast.length > 0 ? (
                    <div className="flex gap-3 overflow-x-auto pb-2">
                      {results.weather.forecast.slice(0, 5).map((day, idx) => (
                        <div key={idx} className="flex-shrink-0 text-center p-4 rounded-xl bg-background/50 border border-border/50 min-w-[100px]">
                          <p className="text-sm text-subtle mb-2">{day.day_of_week?.slice(0, 3) || day.date}</p>
                          {day.icon && <img src={day.icon} alt={day.condition} className="w-10 h-10 mx-auto mb-1" />}
                          <p className="text-2xl font-bold text-foreground">{Math.round(day.temperature?.avg || day.temperature?.max || 0)}°</p>
                          <p className="text-xs text-muted">{day.condition}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted">Weather forecast not available.</p>
                  )}
                </motion.section>

                {/* Attractions */}
                <motion.section variants={itemVariants} className="glass-card glass-card-emerald p-6">
                  <div className="result-header">
                    <div className="result-icon icon-emerald">
                      <MapPin className="w-5 h-5 text-white" />
                    </div>
                    <h3 className="text-xl font-semibold text-foreground">Top Attractions</h3>
                  </div>
                  {results.attractions?.attractions && results.attractions.attractions.length > 0 ? (
                    <div className="grid sm:grid-cols-2 gap-4">
                      {results.attractions.attractions.slice(0, 4).map((place, idx) => (
                        <div key={idx} className="rounded-xl bg-background/50 border border-border/50 p-4">
                          <div className="flex items-start justify-between">
                            <div>
                              <p className="font-medium text-foreground mb-1">{place.name}</p>
                              <p className="text-sm text-muted">{place.types?.[0]?.replace(/_/g, ' ') || 'Attraction'}</p>
                            </div>
                            <div className="flex items-center gap-1 bg-accent-amber/20 px-2 py-1 rounded-full">
                              <Star className="w-3 h-3 text-accent-amber fill-current" />
                              <span className="text-xs text-accent-amber font-medium">{place.rating}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted">No attractions found.</p>
                  )}
                </motion.section>

                {/* Budget */}
                {results.budget && (
                  <motion.section variants={itemVariants} className="glass-card glass-card-cyan p-6">
                    <div className="result-header">
                      <div className="result-icon icon-lime">
                        <DollarSign className="w-5 h-5 text-white" />
                      </div>
                      <h3 className="text-xl font-semibold text-foreground">Budget Estimate</h3>
                    </div>
                    <div className="grid md:grid-cols-2 gap-6">
                      <div className="space-y-3">
                        <div className="flex justify-between items-center p-3 rounded-lg bg-background/50">
                          <span className="text-muted">Flights</span>
                          <span className="text-foreground font-medium">
                            ${results.budget.breakdown?.flights?.total || results.budget.flights?.total || 0}
                          </span>
                        </div>
                        <div className="flex justify-between items-center p-3 rounded-lg bg-background/50">
                          <span className="text-muted">Accommodation</span>
                          <span className="text-foreground font-medium">
                            ${results.budget.breakdown?.accommodation?.total || results.budget.accommodation?.total || 0}
                          </span>
                        </div>
                        <div className="flex justify-between items-center p-3 rounded-lg bg-background/50">
                          <span className="text-muted">Food</span>
                          <span className="text-foreground font-medium">
                            ${results.budget.breakdown?.food?.total || results.budget.food?.total || 0}
                          </span>
                        </div>
                        <div className="flex justify-between items-center p-3 rounded-lg bg-background/50">
                          <span className="text-muted">Activities</span>
                          <span className="text-foreground font-medium">
                            ${results.budget.breakdown?.activities?.total || results.budget.activities?.total || 0}
                          </span>
                        </div>
                        <div className="flex justify-between items-center p-3 rounded-lg bg-background/50">
                          <span className="text-muted">Local Transport</span>
                          <span className="text-foreground font-medium">
                            ${results.budget.breakdown?.local_transport?.total || results.budget.transport?.total || 0}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center justify-center">
                        <div className="text-center p-6 rounded-2xl bg-gradient-to-br from-accent/10 to-accent-violet/10 border border-border">
                          <p className="text-muted mb-2">Total Estimate</p>
                          <p className="text-4xl font-bold text-gradient">
                            ${results.budget.totals?.grand_total || results.budget.totals?.including_flights || 0}
                          </p>
                          <p className="text-sm text-subtle mt-1">for {results.travelers} travelers</p>
                        </div>
                      </div>
                    </div>
                  </motion.section>
                )}
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
