import { Link, useLocation } from 'react-router-dom'
import { Home, Search, FileText, BarChart3, History } from 'lucide-react'
import { clsx } from 'clsx'

const navItems = [
  { path: '/', label: 'Home', icon: Home },
  { path: '/research', label: 'New Research', icon: Search },
  { path: '/reports', label: 'Reports', icon: FileText },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <aside className="fixed left-0 top-16 bottom-0 w-64 glass border-r border-white/10 p-4">
      <nav className="space-y-2">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path
          const Icon = item.icon

          return (
            <Link
              key={item.path}
              to={item.path}
              className={clsx(
                'flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200',
                isActive
                  ? 'bg-primary/20 text-primary border border-primary/30'
                  : 'text-muted-foreground hover:text-white hover:bg-white/5'
              )}
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </Link>
          )
        })}
      </nav>

      <div className="absolute bottom-6 left-4 right-4">
        <div className="glass-card p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-400 to-emerald-600 flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-white" />
            </div>
            <div>
              <p className="text-sm font-medium text-white">API Status</p>
              <p className="text-xs text-green-400">Connected</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <History className="w-3 h-3" />
            <span>Last sync: Just now</span>
          </div>
        </div>
      </div>
    </aside>
  )
}
