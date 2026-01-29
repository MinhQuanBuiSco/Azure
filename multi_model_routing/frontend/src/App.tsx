import { Routes, Route, NavLink } from 'react-router-dom'
import { LayoutDashboard, MessageSquare, BarChart3, Settings, Zap } from 'lucide-react'
import Dashboard from './pages/dashboard'
import Playground from './pages/playground'
import Analytics from './pages/analytics'
import SettingsPage from './pages/settings'
import { clsx } from 'clsx'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-gray-200 bg-white">
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center gap-2 border-b border-gray-200 px-6">
            <Zap className="h-8 w-8 text-blue-600" />
            <span className="text-lg font-semibold text-gray-900">LLM Router</span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 px-3 py-4">
            <NavItem to="/" icon={<LayoutDashboard size={20} />}>
              Dashboard
            </NavItem>
            <NavItem to="/playground" icon={<MessageSquare size={20} />}>
              Playground
            </NavItem>
            <NavItem to="/analytics" icon={<BarChart3 size={20} />}>
              Analytics
            </NavItem>
            <NavItem to="/settings" icon={<Settings size={20} />}>
              Settings
            </NavItem>
          </nav>

          {/* Footer */}
          <div className="border-t border-gray-200 p-4">
            <div className="text-xs text-gray-500">
              Multi-Model LLM Router v0.1.0
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="ml-64 min-h-screen">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/playground" element={<Playground />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  )
}

interface NavItemProps {
  to: string
  icon: React.ReactNode
  children: React.ReactNode
}

function NavItem({ to, icon, children }: NavItemProps) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        clsx(
          'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
          isActive
            ? 'bg-blue-50 text-blue-700'
            : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
        )
      }
    >
      {icon}
      {children}
    </NavLink>
  )
}

export default App
