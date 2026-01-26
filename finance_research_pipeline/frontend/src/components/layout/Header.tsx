import { Link } from 'react-router-dom'
import { TrendingUp, Bell, Settings } from 'lucide-react'
import { Button } from '../ui/button'

export default function Header() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 glass border-b border-white/10">
      <div className="flex items-center justify-between h-full px-6">
        <Link to="/" className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/25">
            <TrendingUp className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">Finance Research</h1>
            <p className="text-xs text-muted-foreground">AI-Powered Analysis</p>
          </div>
        </Link>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-white">
            <Bell className="w-5 h-5" />
          </Button>
          <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-white">
            <Settings className="w-5 h-5" />
          </Button>
        </div>
      </div>
    </header>
  )
}
