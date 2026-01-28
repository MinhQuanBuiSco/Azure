/**
 * API service for Travel Planner backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://travel-mcp-dev-backend.ashydune-af759d06.eastus.azurecontainerapps.io'

export interface TripPlanRequest {
  destination: string
  departure_city: string
  start_date: string
  end_date: string
  travelers: number
  travel_style: string
  interests: string[]
}

export interface HotelImage {
  thumbnail: string
  original_image: string
}

export interface Hotel {
  name: string
  type: string
  description: string
  price_per_night: string
  total_price: string
  currency: string
  rating: number
  reviews_count: number
  star_rating: string
  location: string
  address: string
  amenities: string[]
  images: HotelImage[]
  check_in_time: string
  check_out_time: string
  link?: string
}

export interface Attraction {
  name: string
  rating: number
  types: string[]
  address?: string
  reviews_count?: number
  photo_reference?: string
  place_id?: string
  is_open?: boolean | null
}

export interface WeatherDay {
  date: string
  day_of_week: string
  temperature: {
    min: number
    max: number
    avg: number
  }
  feels_like: {
    min: number
    max: number
  }
  humidity: number
  condition: string
  description: string
  icon: string
}

export interface Flight {
  airline?: string
  flight_number?: string
  origin?: string
  destination?: string
  departure_time?: string
  arrival_time?: string
  duration?: string
  stops?: number
  price?: string
  cabin_class?: string
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type BudgetData = any

export interface TripPlanResponse {
  destination: string
  departure_city?: string
  start_date: string
  end_date: string
  travelers: number
  travel_style: string
  flights?: {
    flights: Flight[]
    error?: string
  }
  hotels: {
    hotels: Hotel[]
    total_results: number
    search_metadata?: Record<string, string>
    error?: string
  }
  attractions: {
    attractions: Attraction[]
    total_results?: number
    total_found?: number
    error?: string
  }
  weather: {
    forecast: WeatherDay[]
    packing_tips?: string[]
    error?: string
  }
  budget: BudgetData
}

export async function fetchTripPlan(request: TripPlanRequest): Promise<TripPlanResponse> {
  const response = await fetch(`${API_BASE_URL}/api/trip-plan`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

export async function fetchHotels(
  location: string,
  checkInDate: string,
  checkOutDate: string,
  guests: number = 2
) {
  const response = await fetch(`${API_BASE_URL}/api/hotels`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      location,
      check_in_date: checkInDate,
      check_out_date: checkOutDate,
      guests,
    }),
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }

  return response.json()
}

export async function fetchAttractions(location: string, maxResults: number = 6) {
  const response = await fetch(`${API_BASE_URL}/api/attractions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      location,
      max_results: maxResults,
    }),
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }

  return response.json()
}

export async function fetchWeather(location: string, startDate?: string, endDate?: string) {
  const response = await fetch(`${API_BASE_URL}/api/weather`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      location,
      start_date: startDate,
      end_date: endDate,
    }),
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }

  return response.json()
}

export async function fetchBudget(
  destination: string,
  days: number,
  travelers: number,
  travelStyle: string
) {
  const response = await fetch(`${API_BASE_URL}/api/budget`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      destination,
      days,
      travelers,
      travel_style: travelStyle,
    }),
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }

  return response.json()
}

// AI Agent Types and Functions
export interface ConversationMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface CollectedParams {
  destination?: string | null
  departure_city?: string | null
  start_date?: string | null
  end_date?: string | null
  travelers?: number | null
  travel_style?: 'budget' | 'moderate' | 'luxury' | null
  interests?: string[]
}

export interface AIAgentRequest {
  query: string
  conversation_history: ConversationMessage[]
  collected_params: CollectedParams
}

export interface AIAgentResponse {
  type: 'conversation' | 'complete'
  message: string
  collected_params: CollectedParams
  missing_fields: string[]
  is_complete: boolean
  trip_plan: TripPlanResponse | null
}

export async function processAIAgentQuery(request: AIAgentRequest): Promise<AIAgentResponse> {
  const response = await fetch(`${API_BASE_URL}/api/ai-agent`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}
