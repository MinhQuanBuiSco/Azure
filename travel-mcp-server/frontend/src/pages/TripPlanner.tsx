import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  MapPin,
  Calendar,
  Users,
  Sparkles,
  Plane,
  Loader2,
  Wallet,
  Heart,
} from 'lucide-react'

type TravelStyle = 'budget' | 'moderate' | 'luxury'

interface TripFormData {
  destination: string
  departureCity: string
  startDate: string
  endDate: string
  travelers: number
  travelStyle: TravelStyle
  interests: string[]
}

const interestOptions = [
  { id: 'culture', label: 'Culture & History', emoji: '' },
  { id: 'food', label: 'Food & Dining', emoji: '' },
  { id: 'nature', label: 'Nature & Outdoors', emoji: '' },
  { id: 'shopping', label: 'Shopping', emoji: '' },
  { id: 'nightlife', label: 'Nightlife', emoji: '' },
  { id: 'relaxation', label: 'Relaxation & Spa', emoji: '' },
]

// Major airports list (used for both departure and destination)
const airports = [
  // Asia
  { code: 'NRT', city: 'Tokyo (Narita)', country: 'Japan', region: 'Asia' },
  { code: 'HND', city: 'Tokyo (Haneda)', country: 'Japan', region: 'Asia' },
  { code: 'KIX', city: 'Osaka', country: 'Japan', region: 'Asia' },
  { code: 'ICN', city: 'Seoul (Incheon)', country: 'South Korea', region: 'Asia' },
  { code: 'PEK', city: 'Beijing', country: 'China', region: 'Asia' },
  { code: 'PVG', city: 'Shanghai', country: 'China', region: 'Asia' },
  { code: 'HKG', city: 'Hong Kong', country: 'Hong Kong', region: 'Asia' },
  { code: 'TPE', city: 'Taipei', country: 'Taiwan', region: 'Asia' },
  { code: 'SIN', city: 'Singapore', country: 'Singapore', region: 'Asia' },
  { code: 'BKK', city: 'Bangkok', country: 'Thailand', region: 'Asia' },
  { code: 'SGN', city: 'Ho Chi Minh City', country: 'Vietnam', region: 'Asia' },
  { code: 'HAN', city: 'Hanoi', country: 'Vietnam', region: 'Asia' },
  { code: 'DAD', city: 'Da Nang', country: 'Vietnam', region: 'Asia' },
  { code: 'MNL', city: 'Manila', country: 'Philippines', region: 'Asia' },
  { code: 'CGK', city: 'Jakarta', country: 'Indonesia', region: 'Asia' },
  { code: 'DPS', city: 'Bali (Denpasar)', country: 'Indonesia', region: 'Asia' },
  { code: 'KUL', city: 'Kuala Lumpur', country: 'Malaysia', region: 'Asia' },
  { code: 'DEL', city: 'New Delhi', country: 'India', region: 'Asia' },
  { code: 'BOM', city: 'Mumbai', country: 'India', region: 'Asia' },
  // Europe
  { code: 'LHR', city: 'London (Heathrow)', country: 'UK', region: 'Europe' },
  { code: 'LGW', city: 'London (Gatwick)', country: 'UK', region: 'Europe' },
  { code: 'CDG', city: 'Paris', country: 'France', region: 'Europe' },
  { code: 'FCO', city: 'Rome', country: 'Italy', region: 'Europe' },
  { code: 'MXP', city: 'Milan', country: 'Italy', region: 'Europe' },
  { code: 'BCN', city: 'Barcelona', country: 'Spain', region: 'Europe' },
  { code: 'MAD', city: 'Madrid', country: 'Spain', region: 'Europe' },
  { code: 'AMS', city: 'Amsterdam', country: 'Netherlands', region: 'Europe' },
  { code: 'FRA', city: 'Frankfurt', country: 'Germany', region: 'Europe' },
  { code: 'MUC', city: 'Munich', country: 'Germany', region: 'Europe' },
  { code: 'ZRH', city: 'Zurich', country: 'Switzerland', region: 'Europe' },
  { code: 'VIE', city: 'Vienna', country: 'Austria', region: 'Europe' },
  { code: 'PRG', city: 'Prague', country: 'Czech Republic', region: 'Europe' },
  { code: 'CPH', city: 'Copenhagen', country: 'Denmark', region: 'Europe' },
  { code: 'ARN', city: 'Stockholm', country: 'Sweden', region: 'Europe' },
  { code: 'HEL', city: 'Helsinki', country: 'Finland', region: 'Europe' },
  { code: 'DUB', city: 'Dublin', country: 'Ireland', region: 'Europe' },
  { code: 'LIS', city: 'Lisbon', country: 'Portugal', region: 'Europe' },
  { code: 'ATH', city: 'Athens', country: 'Greece', region: 'Europe' },
  { code: 'IST', city: 'Istanbul', country: 'Turkey', region: 'Europe' },
  { code: 'KEF', city: 'Reykjavik', country: 'Iceland', region: 'Europe' },
  // North America
  { code: 'SFO', city: 'San Francisco', country: 'USA', region: 'North America' },
  { code: 'LAX', city: 'Los Angeles', country: 'USA', region: 'North America' },
  { code: 'JFK', city: 'New York (JFK)', country: 'USA', region: 'North America' },
  { code: 'EWR', city: 'New York (Newark)', country: 'USA', region: 'North America' },
  { code: 'ORD', city: 'Chicago', country: 'USA', region: 'North America' },
  { code: 'SEA', city: 'Seattle', country: 'USA', region: 'North America' },
  { code: 'MIA', city: 'Miami', country: 'USA', region: 'North America' },
  { code: 'BOS', city: 'Boston', country: 'USA', region: 'North America' },
  { code: 'DFW', city: 'Dallas', country: 'USA', region: 'North America' },
  { code: 'ATL', city: 'Atlanta', country: 'USA', region: 'North America' },
  { code: 'DEN', city: 'Denver', country: 'USA', region: 'North America' },
  { code: 'LAS', city: 'Las Vegas', country: 'USA', region: 'North America' },
  { code: 'HNL', city: 'Honolulu', country: 'USA', region: 'North America' },
  { code: 'YYZ', city: 'Toronto', country: 'Canada', region: 'North America' },
  { code: 'YVR', city: 'Vancouver', country: 'Canada', region: 'North America' },
  { code: 'YUL', city: 'Montreal', country: 'Canada', region: 'North America' },
  { code: 'CUN', city: 'Cancun', country: 'Mexico', region: 'North America' },
  { code: 'MEX', city: 'Mexico City', country: 'Mexico', region: 'North America' },
  // Oceania
  { code: 'SYD', city: 'Sydney', country: 'Australia', region: 'Oceania' },
  { code: 'MEL', city: 'Melbourne', country: 'Australia', region: 'Oceania' },
  { code: 'BNE', city: 'Brisbane', country: 'Australia', region: 'Oceania' },
  { code: 'AKL', city: 'Auckland', country: 'New Zealand', region: 'Oceania' },
  { code: 'NAN', city: 'Fiji (Nadi)', country: 'Fiji', region: 'Oceania' },
  // Middle East
  { code: 'DXB', city: 'Dubai', country: 'UAE', region: 'Middle East' },
  { code: 'AUH', city: 'Abu Dhabi', country: 'UAE', region: 'Middle East' },
  { code: 'DOH', city: 'Doha', country: 'Qatar', region: 'Middle East' },
  { code: 'TLV', city: 'Tel Aviv', country: 'Israel', region: 'Middle East' },
  // South America
  { code: 'GRU', city: 'Sao Paulo', country: 'Brazil', region: 'South America' },
  { code: 'GIG', city: 'Rio de Janeiro', country: 'Brazil', region: 'South America' },
  { code: 'EZE', city: 'Buenos Aires', country: 'Argentina', region: 'South America' },
  { code: 'SCL', city: 'Santiago', country: 'Chile', region: 'South America' },
  { code: 'LIM', city: 'Lima', country: 'Peru', region: 'South America' },
  { code: 'BOG', city: 'Bogota', country: 'Colombia', region: 'South America' },
  // Africa
  { code: 'JNB', city: 'Johannesburg', country: 'South Africa', region: 'Africa' },
  { code: 'CPT', city: 'Cape Town', country: 'South Africa', region: 'Africa' },
  { code: 'CAI', city: 'Cairo', country: 'Egypt', region: 'Africa' },
  { code: 'CMN', city: 'Casablanca', country: 'Morocco', region: 'Africa' },
  { code: 'NBO', city: 'Nairobi', country: 'Kenya', region: 'Africa' },
]

// Group airports by region for better UX
const airportsByRegion = airports.reduce((acc, airport) => {
  if (!acc[airport.region]) {
    acc[airport.region] = []
  }
  acc[airport.region].push(airport)
  return acc
}, {} as Record<string, typeof airports>)

const travelStyles = [
  { id: 'budget', label: 'Budget', description: 'Best value options', icon: Wallet },
  { id: 'moderate', label: 'Moderate', description: 'Balance of comfort & cost', icon: Heart },
  { id: 'luxury', label: 'Luxury', description: 'Premium experiences', icon: Sparkles },
]

export default function TripPlanner() {
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(false)
  const [formData, setFormData] = useState<TripFormData>({
    destination: '',
    departureCity: '',
    startDate: '',
    endDate: '',
    travelers: 2,
    travelStyle: 'moderate',
    interests: ['culture', 'food'],
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    await new Promise((resolve) => setTimeout(resolve, 2000))
    const tripId = Date.now().toString()
    navigate(`/results/${tripId}`, { state: formData })
  }

  const toggleInterest = (interest: string) => {
    setFormData((prev) => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter((i) => i !== interest)
        : [...prev.interests, interest],
    }))
  }

  return (
    <div className="w-full">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="space-y-8"
      >
        {/* Header */}
        <div className="space-y-3 mb-4">
          <h1 className="text-3xl sm:text-4xl font-bold text-foreground">
            Plan Your <span className="text-gradient">Perfect Trip</span>
          </h1>
          <p className="text-muted text-lg">
            Tell us about your dream vacation and let AI do the rest
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-12">
          {/* Location Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-card glass-card-cyan p-8 md:p-10"
          >
            <div className="flex items-center gap-4 mb-8">
              <div className="w-12 h-12 rounded-xl icon-cyan flex items-center justify-center">
                <MapPin className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-foreground">Location</h2>
                <p className="text-sm text-muted">Where are you going?</p>
              </div>
            </div>

            <div className="grid sm:grid-cols-2 gap-5">
              <div className="space-y-2.5">
                <label className="text-sm font-medium text-muted">Destination</label>
                <select
                  className="input-field"
                  value={formData.destination}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, destination: e.target.value }))
                  }
                  required
                >
                  <option value="">Select destination</option>
                  {Object.entries(airportsByRegion).map(([region, regionAirports]) => (
                    <optgroup key={region} label={region}>
                      {regionAirports.map((airport) => (
                        <option key={airport.code} value={airport.code}>
                          {airport.city} ({airport.code}) - {airport.country}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
              </div>
              <div className="space-y-2.5">
                <label className="text-sm font-medium text-muted">Departing From</label>
                <select
                  className="input-field"
                  value={formData.departureCity}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, departureCity: e.target.value }))
                  }
                  required
                >
                  <option value="">Select departure city</option>
                  {Object.entries(airportsByRegion).map(([region, regionAirports]) => (
                    <optgroup key={region} label={region}>
                      {regionAirports.map((airport) => (
                        <option key={airport.code} value={airport.code}>
                          {airport.city} ({airport.code}) - {airport.country}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
              </div>
            </div>
          </motion.div>

          {/* Dates Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-card glass-card-violet p-8 md:p-10"
          >
            <div className="flex items-center gap-4 mb-8">
              <div className="w-12 h-12 rounded-xl icon-violet flex items-center justify-center">
                <Calendar className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-foreground">Travel Dates</h2>
                <p className="text-sm text-muted">When are you traveling?</p>
              </div>
            </div>

            <div className="grid sm:grid-cols-2 gap-5">
              <div className="space-y-2.5">
                <label className="text-sm font-medium text-muted">Start Date</label>
                <input
                  type="date"
                  className="input-field"
                  value={formData.startDate}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, startDate: e.target.value }))
                  }
                  required
                />
              </div>
              <div className="space-y-2.5">
                <label className="text-sm font-medium text-muted">End Date</label>
                <input
                  type="date"
                  className="input-field"
                  value={formData.endDate}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, endDate: e.target.value }))
                  }
                  required
                />
              </div>
            </div>

            <div className="mt-6 space-y-2.5">
              <label className="text-sm font-medium text-muted flex items-center gap-2">
                <Users className="w-4 h-4" />
                Number of Travelers
              </label>
              <input
                type="number"
                min="1"
                max="10"
                className="input-field w-24"
                value={formData.travelers}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    travelers: parseInt(e.target.value) || 1,
                  }))
                }
              />
            </div>
          </motion.div>

          {/* Travel Style Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass-card glass-card-amber p-8 md:p-10"
          >
            <div className="flex items-center gap-4 mb-8">
              <div className="w-12 h-12 rounded-xl icon-amber flex items-center justify-center">
                <Plane className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-foreground">Travel Style</h2>
                <p className="text-sm text-muted">What's your budget preference?</p>
              </div>
            </div>

            <div className="grid sm:grid-cols-3 gap-5">
              {travelStyles.map((style) => {
                const Icon = style.icon
                const isSelected = formData.travelStyle === style.id
                return (
                  <button
                    key={style.id}
                    type="button"
                    onClick={() =>
                      setFormData((prev) => ({ ...prev, travelStyle: style.id as TravelStyle }))
                    }
                    className={`rounded-xl border text-left transition-all ${
                      isSelected
                        ? 'bg-accent/10 border-accent text-foreground'
                        : 'bg-card border-border hover:border-border-hover text-muted hover:text-foreground'
                    }`}
                    style={{ padding: '1.5rem' }}
                  >
                    <Icon className={`w-5 h-5 mb-3 ${isSelected ? 'text-accent' : ''}`} />
                    <div className="font-medium">{style.label}</div>
                    <div className="text-xs text-muted mt-2">{style.description}</div>
                  </button>
                )
              })}
            </div>
          </motion.div>

          {/* Interests Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="glass-card glass-card-emerald p-8 md:p-10"
          >
            <div className="flex items-center gap-4 mb-8">
              <div className="w-12 h-12 rounded-xl icon-emerald flex items-center justify-center">
                <Heart className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-foreground">Interests</h2>
                <p className="text-sm text-muted">What do you enjoy? (Select multiple)</p>
              </div>
            </div>

            <div className="flex flex-wrap gap-3 pb-4">
              {interestOptions.map((interest) => (
                <button
                  key={interest.id}
                  type="button"
                  onClick={() => toggleInterest(interest.id)}
                  className={`selection-btn-pill ${
                    formData.interests.includes(interest.id) ? 'active' : ''
                  }`}
                >
                  {interest.label}
                </button>
              ))}
            </div>
          </motion.div>

          {/* Submit Button */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            style={{ marginTop: '1rem' }}
          >
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full py-4 text-base"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Planning Your Trip...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  Generate Trip Plan
                </>
              )}
            </button>
          </motion.div>
        </form>
      </motion.div>
    </div>
  )
}
