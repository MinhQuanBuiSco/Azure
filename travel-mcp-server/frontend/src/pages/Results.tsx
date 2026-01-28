import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Plane,
  Hotel,
  Sun,
  MapPin,
  DollarSign,
  Star,
  Loader2,
  AlertCircle,
  Clock,
} from 'lucide-react'
import { fetchTripPlan, type TripPlanResponse } from '../services/api'

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

export default function Results() {
  const location = useLocation()
  const tripData = location.state || {
    destination: 'Tokyo, Japan',
    departureCity: 'San Francisco',
    startDate: new Date().toISOString().split('T')[0],
    endDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    travelers: 2,
    travelStyle: 'moderate',
    interests: ['culture', 'food'],
  }

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<TripPlanResponse | null>(null)

  useEffect(() => {
    async function loadTripPlan() {
      try {
        setLoading(true)
        setError(null)

        const result = await fetchTripPlan({
          destination: tripData.destination,
          departure_city: tripData.departureCity || 'San Francisco',
          start_date: tripData.startDate,
          end_date: tripData.endDate,
          travelers: tripData.travelers || 2,
          travel_style: tripData.travelStyle || 'moderate',
          interests: tripData.interests || [],
        })

        setData(result)
      } catch (err) {
        console.error('Failed to fetch trip plan:', err)
        setError(err instanceof Error ? err.message : 'Failed to load trip plan')
      } finally {
        setLoading(false)
      }
    }

    loadTripPlan()
  }, [tripData])

  if (loading) {
    return (
      <div className="w-full max-w-4xl mx-auto flex flex-col items-center justify-center py-20">
        <Loader2 className="w-12 h-12 text-accent animate-spin mb-4" />
        <h2 className="text-xl font-semibold text-foreground mb-2">Planning Your Trip...</h2>
        <p className="text-muted">Fetching hotels, attractions, and weather data</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="w-full max-w-4xl mx-auto flex flex-col items-center justify-center py-20">
        <AlertCircle className="w-12 h-12 text-accent-rose mb-4" />
        <h2 className="text-xl font-semibold text-foreground mb-2">Something went wrong</h2>
        <p className="text-muted mb-4">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="btn-primary"
        >
          Try Again
        </button>
      </div>
    )
  }

  if (!data) return null

  // Extract data with fallbacks
  const flights = data.flights?.flights || []
  const hotels = data.hotels?.hotels || []
  const attractions = data.attractions?.attractions || []
  const weather = data.weather?.forecast || []
  // Budget can be in data.budget.budget or directly in data.budget
  const budget = data.budget?.breakdown ? data.budget : data.budget?.budget

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6 pb-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center mb-6"
      >
        <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-foreground mb-3">
          Your Trip to{' '}
          <span className="text-gradient">
            {tripData.destination || 'Your Destination'}
          </span>
        </h1>
        <p className="text-muted">
          Here's your AI-generated travel plan
        </p>
      </motion.div>

      {/* Results Sections */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="space-y-6"
      >
        {/* Flights */}
        <motion.section variants={itemVariants} className="glass-card glass-card-cyan p-6 md:p-8">
          <div className="result-header">
            <div className="result-icon icon-cyan">
              <Plane className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-xl font-semibold text-foreground">
              Flights
            </h2>
          </div>
          {flights.length > 0 ? (
            <div className="space-y-3">
              {flights.slice(0, 3).map((flight: any, idx: number) => (
                <div
                  key={idx}
                  className="rounded-xl bg-background/50 hover:bg-card-hover/50 transition-all border border-border/50 p-4 hover:border-border-hover"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="text-center">
                        <p className="text-lg font-semibold text-foreground">{flight.departure_time || '--:--'}</p>
                        <p className="text-xs text-muted">{flight.origin || tripData.departureCity}</p>
                      </div>
                      <div className="flex items-center gap-2 text-muted">
                        <div className="w-8 h-px bg-border"></div>
                        <Plane className="w-4 h-4" />
                        <div className="w-8 h-px bg-border"></div>
                      </div>
                      <div className="text-center">
                        <p className="text-lg font-semibold text-foreground">{flight.arrival_time || '--:--'}</p>
                        <p className="text-xs text-muted">{flight.destination || tripData.destination}</p>
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
                      {flight.stops !== undefined && (
                        <span className="ml-2">• {flight.stops === 0 ? 'Direct' : `${flight.stops} stop${flight.stops > 1 ? 's' : ''}`}</span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted">Flight information not available. Check airlines directly for best prices.</p>
          )}
        </motion.section>

        {/* Hotels */}
        <motion.section variants={itemVariants} className="glass-card glass-card-violet p-6 md:p-8">
          <div className="result-header">
            <div className="result-icon icon-violet">
              <Hotel className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-xl font-semibold text-foreground">
              Hotels
            </h2>
          </div>
          {hotels.length > 0 ? (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {hotels.slice(0, 3).map((hotel, idx) => (
                <div
                  key={idx}
                  className="rounded-xl bg-background/50 hover:bg-card-hover/50 transition-all border border-border/50 overflow-hidden hover:border-border-hover hover:shadow-lg"
                >
                  {hotel.images && hotel.images[0] && (
                    <div className="relative h-36 overflow-hidden">
                      <img
                        src={hotel.images[0].thumbnail || hotel.images[0].original_image}
                        alt={hotel.name}
                        className="w-full h-full object-cover transition-transform duration-300 hover:scale-105"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none'
                        }}
                      />
                    </div>
                  )}
                  <div className="p-4">
                    <p className="font-medium text-foreground mb-2">
                      {hotel.name}
                    </p>
                    <div className="flex items-center gap-2 mb-2">
                      <Star className="w-4 h-4 text-accent-amber fill-current" />
                      <span className="text-sm text-muted">
                        {hotel.rating}
                      </span>
                      <span className="text-sm text-subtle">
                        • {hotel.location}
                      </span>
                    </div>
                    <p className="text-lg font-bold text-accent-violet">
                      {hotel.price_per_night}
                      <span className="text-sm font-normal text-subtle">
                        /night
                      </span>
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted">No hotels found for this destination.</p>
          )}
        </motion.section>

        {/* Weather */}
        <motion.section variants={itemVariants} className="glass-card glass-card-amber p-6 md:p-8">
          <div className="result-header">
            <div className="result-icon icon-amber">
              <Sun className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-xl font-semibold text-foreground">
              Weather Forecast
            </h2>
          </div>
          {weather.length > 0 ? (
            <div className="flex gap-3 overflow-x-auto pb-2 -mx-2 px-2">
              {weather.slice(0, 5).map((day, idx) => (
                <div
                  key={idx}
                  className="flex-shrink-0 text-center p-4 rounded-xl bg-background/50 border border-border/50 min-w-[100px]"
                >
                  <p className="text-sm text-subtle mb-2">
                    {day.day_of_week?.slice(0, 3) || day.date}
                  </p>
                  {day.icon && (
                    <img
                      src={day.icon}
                      alt={day.condition}
                      className="w-10 h-10 mx-auto mb-1"
                    />
                  )}
                  <p className="text-2xl font-bold text-foreground mb-1">
                    {Math.round(day.temperature?.avg || day.temperature?.max || 0)}°
                  </p>
                  <p className="text-xs text-muted">
                    {day.condition}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted">Weather forecast not available.</p>
          )}
        </motion.section>

        {/* Attractions */}
        <motion.section variants={itemVariants} className="glass-card glass-card-emerald p-6 md:p-8">
          <div className="result-header">
            <div className="result-icon icon-emerald">
              <MapPin className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-xl font-semibold text-foreground">
              Top Attractions
            </h2>
          </div>
          {attractions.length > 0 ? (
            <div className="grid sm:grid-cols-2 gap-4">
              {attractions.slice(0, 4).map((place, idx) => (
                <div
                  key={idx}
                  className="rounded-xl bg-background/50 hover:bg-card-hover/50 transition-all border border-border/50 overflow-hidden hover:border-border-hover hover:shadow-lg p-4"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="font-medium text-foreground mb-1">
                        {place.name}
                      </p>
                      <p className="text-sm text-muted mb-2">
                        {place.types?.[0]?.replace(/_/g, ' ') || 'Attraction'}
                      </p>
                      {place.address && (
                        <p className="text-xs text-subtle">
                          {place.address}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-1 bg-accent-amber/20 px-2 py-1 rounded-full ml-2">
                      <Star className="w-3 h-3 text-accent-amber fill-current" />
                      <span className="text-xs text-accent-amber font-medium">
                        {place.rating}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted">No attractions found for this destination.</p>
          )}
        </motion.section>

        {/* Budget Summary */}
        {budget && (
          <motion.section variants={itemVariants} className="glass-card glass-card-cyan p-6 md:p-8">
            <div className="result-header">
              <div className="result-icon icon-lime">
                <DollarSign className="w-5 h-5 text-white" />
              </div>
              <h2 className="text-xl font-semibold text-foreground">
                Budget Estimate
              </h2>
            </div>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-muted">Flights</span>
                  <span className="text-foreground font-medium">
                    ${budget.breakdown?.flights?.total || budget.flights?.total || 0}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted">Accommodation</span>
                  <span className="text-foreground font-medium">
                    ${budget.breakdown?.accommodation?.total || budget.accommodation?.total || 0}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted">Food</span>
                  <span className="text-foreground font-medium">
                    ${budget.breakdown?.food?.total || budget.food?.total || 0}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted">Activities</span>
                  <span className="text-foreground font-medium">
                    ${budget.breakdown?.activities?.total || budget.activities?.total || 0}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted">Transport</span>
                  <span className="text-foreground font-medium">
                    ${budget.breakdown?.local_transport?.total || budget.transport?.total || 0}
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-center">
                <div className="text-center p-6 rounded-2xl bg-gradient-to-br from-accent/10 to-accent-violet/10 border border-border">
                  <p className="text-muted mb-2">
                    Total Estimate
                  </p>
                  <p className="text-4xl font-bold text-gradient">
                    ${budget.totals?.grand_total || budget.totals?.including_flights || 0}
                  </p>
                  <p className="text-sm text-subtle mt-1">
                    for {tripData.travelers || 2} travelers
                  </p>
                </div>
              </div>
            </div>
          </motion.section>
        )}
      </motion.div>
    </div>
  )
}
