import { Link, useLocation } from 'react-router-dom'
import { Plane, Sparkles, Map, Bot } from 'lucide-react'
import { motion } from 'framer-motion'

export default function Header() {
  const location = useLocation()

  const navItems = [
    { path: '/', label: 'Home', icon: Sparkles },
    { path: '/planner', label: 'Plan Trip', icon: Map },
    { path: '/ai-agent', label: 'AI Agent', icon: Bot },
  ]

  return (
    <header className="sticky top-0 z-50 w-full backdrop-blur-md bg-background/80 border-b border-border/50 flex flex-col items-center">
      <div className="w-full max-w-4xl px-8">
        <nav className="h-16 flex items-center justify-between">
          {/* Logo */}
          <Link
            to="/"
            className="flex items-center gap-3 group"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent to-accent-violet flex items-center justify-center shadow-lg shadow-accent/20 group-hover:shadow-accent/40 transition-shadow duration-300">
              <Plane className="w-5 h-5 text-background" />
            </div>
            <span className="text-lg font-semibold text-gradient hidden sm:block">
              Travel Planner
            </span>
          </Link>

          {/* Navigation */}
          <div className="flex items-center gap-2">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path
              const Icon = item.icon

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className="relative px-4 py-2.5 rounded-lg"
                >
                  {isActive && (
                    <motion.div
                      layoutId="nav-indicator"
                      className="absolute inset-0 bg-accent/10 border border-accent/30 rounded-lg"
                      transition={{
                        type: 'spring',
                        stiffness: 400,
                        damping: 30,
                      }}
                    />
                  )}
                  <span
                    className={`relative flex items-center gap-2 text-base font-medium transition-colors duration-200 ${
                      isActive
                        ? 'text-accent'
                        : 'text-muted hover:text-foreground'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{item.label}</span>
                  </span>
                </Link>
              )
            })}
          </div>
        </nav>
      </div>
    </header>
  )
}
