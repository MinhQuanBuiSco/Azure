import { Link, Outlet, useLocation } from "react-router-dom"
import { cn } from "../lib/utils"
import { Shield, LayoutDashboard, CreditCard, AlertTriangle, BarChart3, Moon, Sun, Activity } from "lucide-react"
import { useTheme } from "../contexts/ThemeContext"
import { useTransactionFeed } from "../contexts/WebSocketContext"

function useNavigation() {
  const { stats } = useTransactionFeed();

  return [
    { name: "Dashboard", href: "/", icon: LayoutDashboard, badge: null },
    { name: "Transactions", href: "/transactions", icon: CreditCard, badge: null },
    { name: "Alerts", href: "/alerts", icon: AlertTriangle, badge: stats.pendingAlerts > 0 ? stats.pendingAlerts.toString() : null },
    { name: "Analytics", href: "/analytics", icon: BarChart3, badge: null },
  ];
}

export default function Layout() {
  const location = useLocation()
  const { theme, toggleTheme } = useTheme()
  const navigation = useNavigation()

  return (
    <div className="min-h-screen bg-background">
      {/* Modern Sidebar with Glass Effect */}
      <div className="hidden md:fixed md:inset-y-0 md:flex md:w-72 md:flex-col z-50">
        <div className="flex flex-col flex-grow border-r border-border/50 bg-card/95 backdrop-blur-xl pt-6 pb-4 overflow-y-auto shadow-2xl">
          {/* Logo Section */}
          <div className="flex items-center flex-shrink-0 px-6 mb-8">
            <div className="relative">
              <div className="absolute inset-0 bg-primary/20 rounded-xl blur-lg" />
              <div className="relative p-2 bg-gradient-to-br from-primary to-primary/60 rounded-xl shadow-lg">
                <Shield className="h-7 w-7 text-white" />
              </div>
            </div>
            <div className="ml-3">
              <span className="text-xl font-black bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                FraudShield
              </span>
              <p className="text-xs text-muted-foreground font-medium">AI-Powered Protection</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex-1 px-3 space-y-2">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href ||
                (item.href !== "/" && location.pathname.startsWith(item.href))

              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    "group relative flex items-center px-4 py-3.5 text-sm font-semibold rounded-xl transition-all duration-300",
                    isActive
                      ? "bg-primary text-primary-foreground shadow-lg shadow-primary/30"
                      : "text-muted-foreground hover:bg-accent/50 hover:text-accent-foreground"
                  )}
                >
                  {/* Active indicator bar */}
                  {isActive && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-primary-foreground rounded-r-full" />
                  )}

                  <item.icon
                    className={cn(
                      "mr-3 flex-shrink-0 h-5 w-5 transition-transform duration-300 group-hover:scale-110",
                      isActive ? "text-primary-foreground" : "text-muted-foreground"
                    )}
                  />
                  <span className="flex-1">{item.name}</span>

                  {/* Badge */}
                  {item.badge && (
                    <span className="ml-auto px-2 py-0.5 text-xs font-bold bg-destructive text-destructive-foreground rounded-full">
                      {item.badge}
                    </span>
                  )}

                  {/* Hover glow effect */}
                  {!isActive && (
                    <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-primary/0 via-primary/5 to-primary/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  )}
                </Link>
              )
            })}
          </nav>

          {/* Bottom Section */}
          <div className="flex-shrink-0 border-t border-border/50 p-4 space-y-3">
            {/* System Status */}
            <div className="px-3 py-3 bg-success/10 border border-success/20 rounded-xl">
              <div className="flex items-center gap-2 mb-1">
                <div className="relative">
                  <Activity className="h-4 w-4 text-success" />
                  <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-success rounded-full animate-pulse" />
                </div>
                <p className="text-xs font-bold text-success">System Online</p>
              </div>
              <p className="text-xs text-muted-foreground">All services operational</p>
            </div>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="flex items-center w-full px-4 py-3 text-sm font-semibold rounded-xl text-muted-foreground hover:bg-accent/50 hover:text-accent-foreground transition-all duration-300 group"
            >
              <div className="p-2 bg-accent/50 rounded-lg mr-3 group-hover:bg-accent transition-colors">
                {theme === 'dark' ? (
                  <Sun className="h-4 w-4" />
                ) : (
                  <Moon className="h-4 w-4" />
                )}
              </div>
              <span className="flex-1 text-left">
                {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Main content with backdrop */}
      <div className="md:pl-72 flex flex-col flex-1 min-h-screen">
        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
