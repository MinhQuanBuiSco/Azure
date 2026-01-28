export interface Flight {
  airline: string
  flightNumber: string
  price: number
  currency: string
  departureTime: string
  departureAirport: string
  arrivalTime: string
  arrivalAirport: string
  duration: number
  stops: number
  carbonEmissions?: number
}

export interface Hotel {
  name: string
  type: string
  description: string
  pricePerNight: string
  totalPrice: string
  currency: string
  rating: number
  reviewsCount: number
  starRating: string
  location: string
  address: string
  amenities: string[]
  checkInTime: string
  checkOutTime: string
}

export interface WeatherForecast {
  date: string
  dayOfWeek: string
  temperature: {
    min: number
    max: number
    avg: number
  }
  humidity: number
  condition: string
  description: string
  icon: string
}

export interface Attraction {
  name: string
  address: string
  rating: number
  reviewsCount: number
  types: string[]
  isOpen?: boolean
  description?: string
}

export interface Restaurant {
  name: string
  address: string
  rating: number
  reviewsCount: number
  priceLevel: number
  priceSymbol: string
  cuisine: string
  isOpen?: boolean
}

export interface ExchangeRate {
  fromCurrency: string
  toCurrency: string
  rate: number
  amount: number
  convertedAmount: number
  lastUpdated: string
}

export interface VisaInfo {
  passportCountry: string
  destination: string
  visaType: string
  visaTypeDescription: string
  allowedStay: string
  notes: string
  recommendations: string[]
}

export interface BudgetBreakdown {
  flights: { perPerson: number; total: number }
  accommodation: { perNight: number; nights: number; total: number }
  food: { perDay: number; days: number; total: number }
  activities: { perDay: number; days: number; total: number }
  localTransport: { perDay: number; days: number; total: number }
  miscellaneous: { perDay: number; days: number; total: number }
}

export interface Budget {
  destination: string
  duration: string
  travelers: number
  travelStyle: string
  currency: string
  breakdown: BudgetBreakdown
  totals: {
    excludingFlights: number
    grandTotal: number
    perPerson: number
    perDay: number
  }
  tips: string[]
}

export interface TripPlan {
  destination: string
  duration: string
  pace: string
  interests: string[]
  itinerary: DayPlan[]
  generalTips: string[]
}

export interface DayPlan {
  day: number
  theme: string
  activities: Activity[]
  meals: {
    breakfast: string
    lunch: string
    dinner: string
  }
  tips: string[]
}

export interface Activity {
  name: string
  duration: string
  cost: string
  timeSlot: string
}

export interface TripFormData {
  destination: string
  departureCity: string
  startDate: string
  endDate: string
  travelers: number
  travelStyle: 'budget' | 'moderate' | 'luxury'
  interests: string[]
}
