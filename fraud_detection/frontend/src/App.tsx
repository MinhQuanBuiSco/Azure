import { BrowserRouter, Routes, Route } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ThemeProvider } from "./contexts/ThemeContext"
import { WebSocketProvider } from "./contexts/WebSocketContext"
import Layout from "./components/Layout"
import Dashboard from "./pages/Dashboard"
import Transactions from "./pages/Transactions"
import TransactionDetail from "./pages/TransactionDetail"
import Alerts from "./pages/Alerts"
import Analytics from "./pages/Analytics"

const queryClient = new QueryClient()

function App() {
  return (
    <WebSocketProvider>
      <ThemeProvider>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Layout />}>
                <Route index element={<Dashboard />} />
                <Route path="transactions" element={<Transactions />} />
                <Route path="transactions/:id" element={<TransactionDetail />} />
                <Route path="alerts" element={<Alerts />} />
                <Route path="analytics" element={<Analytics />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </QueryClientProvider>
      </ThemeProvider>
    </WebSocketProvider>
  )
}

export default App
