/**
 * Live dashboard with real-time fraud detection monitoring
 */
import { useNavigate } from 'react-router-dom';
import { useTransactionFeed } from '../contexts/WebSocketContext';
import { StatCard } from '../components/StatCard';
import { TransactionCard } from '../components/TransactionCard';

export default function Dashboard() {
  const navigate = useNavigate();

  // Use the global WebSocket context - won't disconnect on theme changes
  const { isConnected, transactions, stats } = useTransactionFeed();

  const fraudRate =
    stats.totalToday > 0
      ? ((stats.fraudDetected / stats.totalToday) * 100).toFixed(1)
      : '0.0';

  return (
    <div className="flex-1 space-y-8 p-8 pt-6">
      {/* Header with gradient backdrop */}
      <div className="relative">
        <div className="absolute inset-0 bg-gradient-to-r from-primary/10 via-primary/5 to-transparent rounded-3xl -z-10 blur-3xl" />
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h2 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
              Live Dashboard
            </h2>
            <p className="text-muted-foreground flex items-center gap-2">
              <span className="inline-block w-2 h-2 bg-primary rounded-full pulse-dot" />
              Real-time fraud detection monitoring
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div
              className={`relative flex items-center gap-2 px-4 py-2 rounded-2xl text-sm font-semibold transition-all duration-300 ${
                isConnected
                  ? 'bg-success/10 text-success border border-success/20 shadow-lg shadow-success/10'
                  : 'bg-destructive/10 text-destructive border border-destructive/20'
              }`}
            >
              <span
                className={`relative w-2.5 h-2.5 rounded-full ${
                  isConnected ? 'bg-success' : 'bg-destructive'
                }`}
              >
                {isConnected && (
                  <span className="absolute inset-0 rounded-full bg-success animate-ping opacity-75" />
                )}
              </span>
              {isConnected ? 'Live' : 'Disconnected'}
            </div>
          </div>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Transactions"
          value={stats.totalToday.toLocaleString()}
          subtitle="Today"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
          }
        />

        <StatCard
          title="Fraud Detected"
          value={stats.fraudDetected}
          subtitle={`${fraudRate}% fraud rate`}
          variant={stats.fraudDetected > 0 ? 'danger' : 'success'}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          }
        />

        <StatCard
          title="Amount Blocked"
          value={`$${stats.amountBlocked.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}`}
          subtitle="Protected from fraud"
          variant={stats.amountBlocked > 0 ? 'warning' : 'default'}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
          }
        />

        <StatCard
          title="Pending Alerts"
          value={stats.pendingAlerts}
          subtitle="Requires investigation"
          variant={stats.pendingAlerts > 5 ? 'warning' : 'default'}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
              />
            </svg>
          }
        />
      </div>

      {/* Transaction Feed */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main feed */}
        <div className="lg:col-span-2">
          <div className="bg-card rounded-2xl border border-border shadow-xl backdrop-blur-sm transition-all duration-300 hover:shadow-2xl overflow-hidden">
            <div className="px-6 py-5 border-b border-border bg-gradient-to-r from-primary/5 to-transparent">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary/10 rounded-xl">
                  <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-card-foreground">
                    Live Transaction Feed
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Real-time fraud detection results
                  </p>
                </div>
              </div>
            </div>
            <div className="p-4 space-y-3 max-h-[600px] overflow-y-auto custom-scrollbar">
              {transactions.length === 0 ? (
                <div className="text-center py-16">
                  <div className="relative w-16 h-16 mx-auto mb-6">
                    <div className="absolute inset-0 bg-primary/20 rounded-full animate-ping" />
                    <div className="relative flex items-center justify-center w-16 h-16 bg-primary/10 rounded-full">
                      <svg
                        className="w-8 h-8 text-primary"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                    </div>
                  </div>
                  <p className="text-muted-foreground font-medium">
                    {isConnected
                      ? 'Waiting for transactions...'
                      : 'Connecting to live feed...'}
                  </p>
                  <p className="text-sm text-muted-foreground/70 mt-3">
                    Run <code className="px-3 py-1.5 bg-muted text-foreground rounded-lg font-mono text-xs">make generate-txns</code> to generate test transactions
                  </p>
                </div>
              ) : (
                transactions.map((txn) => (
                  <TransactionCard
                    key={txn.transaction_id}
                    transaction={txn}
                    onClick={() => navigate(`/transactions/${txn.transaction_id}`)}
                  />
                ))
              )}
            </div>
          </div>
        </div>

        {/* Fraud Alerts Sidebar */}
        <div className="lg:col-span-1">
          <div className="bg-card rounded-2xl border border-border shadow-xl backdrop-blur-sm transition-all duration-300 hover:shadow-2xl overflow-hidden">
            <div className="px-6 py-5 border-b border-border bg-gradient-to-r from-destructive/10 to-transparent">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-destructive/10 rounded-xl">
                  <svg className="w-5 h-5 text-destructive" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-card-foreground">Fraud Alerts</h3>
                  <p className="text-sm text-muted-foreground">High-risk transactions</p>
                </div>
              </div>
            </div>
            <div className="p-4 space-y-3 max-h-[600px] overflow-y-auto custom-scrollbar">
              {transactions.filter((t) => t.is_fraud).length === 0 ? (
                <div className="text-center py-12">
                  <div className="relative w-14 h-14 mx-auto mb-4">
                    <div className="absolute inset-0 bg-success/20 rounded-full blur-lg" />
                    <div className="relative flex items-center justify-center w-14 h-14 bg-success/10 rounded-full">
                      <svg
                        className="w-7 h-7 text-success"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                        />
                      </svg>
                    </div>
                  </div>
                  <p className="text-sm font-medium text-success">All Clear</p>
                  <p className="text-xs text-muted-foreground mt-1">No fraud detected</p>
                </div>
              ) : (
                transactions
                  .filter((t) => t.is_fraud)
                  .map((txn) => (
                    <div
                      key={txn.transaction_id}
                      className="group relative p-4 rounded-xl bg-destructive/5 border border-destructive/20 hover:border-destructive/40 transition-all duration-300 cursor-pointer hover:shadow-lg hover:shadow-destructive/10"
                      onClick={() => navigate(`/transactions/${txn.transaction_id}`)}
                    >
                      <div className="absolute top-2 right-2">
                        <span className="px-2.5 py-1 text-xs font-bold bg-destructive text-destructive-foreground rounded-lg shadow-lg">
                          FRAUD
                        </span>
                      </div>
                      <div className="pr-16">
                        <span className="text-xs font-mono text-muted-foreground">
                          {txn.transaction_id.slice(0, 8)}
                        </span>
                        <p className="text-lg font-bold text-card-foreground mt-2">
                          ${txn.amount.toFixed(2)}
                        </p>
                        <p className="text-sm text-muted-foreground truncate">{txn.merchant_name}</p>
                        <div className="flex items-center gap-2 mt-3">
                          <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-warning via-destructive to-destructive rounded-full"
                              style={{ width: `${txn.fraud_score}%` }}
                            />
                          </div>
                          <span className="text-xs font-bold text-destructive">
                            {txn.fraud_score.toFixed(0)}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
