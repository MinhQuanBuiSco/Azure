/**
 * Alert queue and case management page
 * Uses alerts from global WebSocketContext for persistence across navigation
 */
import { useState, useMemo } from 'react';
import { useTransactionFeed } from '../contexts/WebSocketContext';
import { AlertCard, Alert } from '../components/AlertCard';
import { StatCard } from '../components/StatCard';

type StatusFilter = 'all' | Alert['status'];
type PriorityFilter = 'all' | Alert['priority'];

export default function Alerts() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [priorityFilter, setPriorityFilter] = useState<PriorityFilter>('all');

  // Use alerts from the global WebSocket context
  const { isAlertsConnected, alerts, updateAlertStatus } = useTransactionFeed();

  function handleStatusChange(alertId: string, newStatus: Alert['status']) {
    updateAlertStatus(alertId, newStatus);
  }

  function handleAssign(alertId: string, assignee: string) {
    // For now, this is a no-op since we don't have assign functionality in context
    console.log('Assign alert', alertId, 'to', assignee);
  }

  // Filter alerts
  const filteredAlerts = useMemo(() => {
    return alerts.filter((alert) => {
      const statusMatch = statusFilter === 'all' || alert.status === statusFilter;
      const priorityMatch = priorityFilter === 'all' || alert.priority === priorityFilter;
      return statusMatch && priorityMatch;
    });
  }, [alerts, statusFilter, priorityFilter]);

  // Calculate stats
  const stats = useMemo(() => ({
    total: alerts.length,
    new: alerts.filter((a) => a.status === 'new').length,
    investigating: alerts.filter((a) => a.status === 'investigating').length,
    resolved: alerts.filter((a) => a.status === 'resolved').length,
    critical: alerts.filter((a) => a.priority === 'critical').length,
  }), [alerts]);

  return (
    <div className="flex-1 space-y-6 p-8 pt-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Alert Queue</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Fraud detection alerts requiring investigation
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${
              isAlertsConnected
                ? 'bg-success/10 text-success border border-success/20'
                : 'bg-destructive/10 text-destructive border border-destructive/20'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isAlertsConnected ? 'bg-success animate-pulse' : 'bg-destructive'
              }`}
            />
            {isAlertsConnected ? 'Live' : 'Disconnected'}
          </div>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <StatCard
          title="Total Alerts"
          value={stats.total}
          subtitle="All time"
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

        <StatCard
          title="New"
          value={stats.new}
          subtitle="Awaiting review"
          variant={stats.new > 0 ? 'danger' : 'default'}
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
          title="Investigating"
          value={stats.investigating}
          subtitle="In progress"
          variant={stats.investigating > 0 ? 'warning' : 'default'}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          }
        />

        <StatCard
          title="Resolved"
          value={stats.resolved}
          subtitle="Completed"
          variant="success"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          }
        />

        <StatCard
          title="Critical"
          value={stats.critical}
          subtitle="High priority"
          variant={stats.critical > 0 ? 'danger' : 'default'}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          }
        />
      </div>

      {/* Filters */}
      <div className="bg-card rounded-lg border border-border shadow-sm p-4">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-foreground">Status:</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
              className="px-3 py-1.5 border border-input rounded-lg text-sm bg-background focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="all">All Statuses</option>
              <option value="new">New</option>
              <option value="investigating">Investigating</option>
              <option value="resolved">Resolved</option>
              <option value="false_positive">False Positive</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-foreground">Priority:</label>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value as PriorityFilter)}
              className="px-3 py-1.5 border border-input rounded-lg text-sm bg-background focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="all">All Priorities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          {(statusFilter !== 'all' || priorityFilter !== 'all') && (
            <button
              onClick={() => {
                setStatusFilter('all');
                setPriorityFilter('all');
              }}
              className="px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground underline"
            >
              Clear filters
            </button>
          )}

          <div className="ml-auto text-sm text-muted-foreground">
            Showing {filteredAlerts.length} of {alerts.length} alerts
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="bg-card rounded-lg border border-border shadow-sm">
        <div className="px-6 py-4 border-b border-border">
          <h3 className="text-lg font-semibold text-card-foreground">
            {statusFilter === 'all' ? 'All Alerts' : `${statusFilter.replace('_', ' ')} Alerts`.replace(/\b\w/g, l => l.toUpperCase())}
          </h3>
          <p className="text-sm text-muted-foreground mt-1">
            Manage and investigate fraud alerts
          </p>
        </div>

        <div className="p-4 space-y-3 max-h-[800px] overflow-y-auto custom-scrollbar">
          {filteredAlerts.length === 0 ? (
            <div className="text-center py-12">
              {alerts.length === 0 ? (
                <>
                  <svg
                    className="w-12 h-12 text-success mx-auto mb-4"
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
                  <p className="text-muted-foreground">No fraud alerts</p>
                  <p className="text-sm text-muted-foreground/70 mt-2">
                    {isAlertsConnected
                      ? 'Monitoring for suspicious activity...'
                      : 'Connecting to alert stream...'}
                  </p>
                  <p className="text-sm text-muted-foreground/70 mt-2">
                    Generate test transactions with{' '}
                    <code className="px-2 py-1 bg-muted text-foreground rounded">make generate-txns</code>
                  </p>
                </>
              ) : (
                <>
                  <svg
                    className="w-12 h-12 text-muted-foreground mx-auto mb-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
                    />
                  </svg>
                  <p className="text-muted-foreground">No alerts match your filters</p>
                  <p className="text-sm text-muted-foreground/70 mt-2">
                    Try adjusting your filter criteria
                  </p>
                </>
              )}
            </div>
          ) : (
            filteredAlerts.map((alert) => (
              <AlertCard
                key={alert.id}
                alert={alert}
                onStatusChange={handleStatusChange}
                onAssign={handleAssign}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
