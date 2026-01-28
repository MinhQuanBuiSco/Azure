import { Outlet } from 'react-router-dom'
import Header from './Header'

export default function Layout() {
  return (
    <div className="min-h-screen w-full flex flex-col">
      <Header />

      <main className="flex-1 w-full flex flex-col items-center">
        <div className="w-full max-w-4xl px-8 py-10">
          <Outlet />
        </div>
      </main>

      <footer className="w-full py-8 mt-auto border-t border-border/50 flex flex-col items-center">
        <div className="w-full max-w-4xl px-8">
          <div className="flex flex-col items-center justify-center gap-2 text-center">
            <p className="text-sm text-muted">
              Powered by MCP (Model Context Protocol)
            </p>
            <div className="flex items-center gap-1.5 text-xs text-subtle">
              <span>Built with</span>
              <span className="text-gradient font-medium">AI</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
