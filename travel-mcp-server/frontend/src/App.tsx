import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Home from './pages/Home'
import TripPlanner from './pages/TripPlanner'
import Results from './pages/Results'
import AIAgent from './pages/AIAgent'

function App() {
  return (
    <div className="min-h-screen w-full bg-background">
      {/* Simple gradient background */}
      <div className="app-background" aria-hidden="true" />

      {/* Main content */}
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="planner" element={<TripPlanner />} />
          <Route path="results/:tripId" element={<Results />} />
          <Route path="ai-agent" element={<AIAgent />} />
        </Route>
      </Routes>
    </div>
  )
}

export default App
