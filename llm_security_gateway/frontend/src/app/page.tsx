"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/shared/header";
import { StatsCards } from "@/components/dashboard/stats-cards";
import { RecentRequests } from "@/components/dashboard/recent-requests";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { getAuditSummary, getAuditLogs, getThreatAnalytics, type AuditLog, type AuditLogSummary } from "@/lib/api";
import { RefreshCw } from "lucide-react";

export default function DashboardPage() {
  const [period, setPeriod] = useState("24h");
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState<AuditLogSummary>({
    total_requests: 0,
    allowed_requests: 0,
    blocked_requests: 0,
    filtered_requests: 0,
    error_requests: 0,
    total_tokens: 0,
    prompt_tokens: 0,
    completion_tokens: 0,
    avg_response_time_ms: 0,
  });
  const [recentLogs, setRecentLogs] = useState<AuditLog[]>([]);
  const [threatStats, setThreatStats] = useState<{
    total_threats: number;
    by_type: Record<string, number>;
    by_severity: Record<string, number>;
  } | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [summaryData, logsData, threatsData] = await Promise.all([
        getAuditSummary(period).catch(() => stats),
        getAuditLogs({ limit: 10 }).catch(() => ({ logs: [], count: 0 })),
        getThreatAnalytics(period).catch(() => null),
      ]);
      setStats(summaryData);
      setRecentLogs(logsData.logs);
      setThreatStats(threatsData);
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [period]);

  return (
    <div className="flex flex-col h-full">
      <Header
        title="Dashboard"
        description="Overview of your LLM Security Gateway"
        actions={
          <div className="flex items-center gap-2">
            <Select value={period} onValueChange={setPeriod}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1h">Last Hour</SelectItem>
                <SelectItem value="24h">Last 24h</SelectItem>
                <SelectItem value="7d">Last 7 Days</SelectItem>
                <SelectItem value="30d">Last 30 Days</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="icon" onClick={fetchData}>
              <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            </Button>
          </div>
        }
      />

      <div className="flex-1 overflow-auto p-6 space-y-6">
        {/* Stats Cards */}
        <StatsCards stats={stats} />

        {/* Charts and Lists */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Threat Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>Threat Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              {threatStats && threatStats.total_threats > 0 ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    {Object.entries(threatStats.by_type).map(([type, count]) => (
                      <div key={type} className="flex justify-between items-center">
                        <span className="text-sm capitalize">
                          {type.replace("_", " ")}
                        </span>
                        <span className="font-semibold">{count}</span>
                      </div>
                    ))}
                  </div>
                  <div className="border-t pt-4">
                    <h4 className="text-sm font-medium mb-2">By Severity</h4>
                    <div className="grid grid-cols-4 gap-2">
                      {["critical", "high", "medium", "low"].map((severity) => (
                        <div key={severity} className="text-center">
                          <div
                            className={`text-lg font-bold ${
                              severity === "critical"
                                ? "text-red-600"
                                : severity === "high"
                                ? "text-orange-600"
                                : severity === "medium"
                                ? "text-yellow-600"
                                : "text-blue-600"
                            }`}
                          >
                            {threatStats.by_severity[severity] || 0}
                          </div>
                          <div className="text-xs text-gray-500 capitalize">
                            {severity}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-center text-gray-500 py-8">
                  No threats detected in this period
                </p>
              )}
            </CardContent>
          </Card>

          {/* Recent Requests */}
          <RecentRequests logs={recentLogs} />
        </div>

        {/* Request Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Request Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <div className="flex h-4 overflow-hidden rounded-full bg-gray-100">
                  {stats.total_requests > 0 && (
                    <>
                      <div
                        className="bg-green-500"
                        style={{
                          width: `${(stats.allowed_requests / stats.total_requests) * 100}%`,
                        }}
                      />
                      <div
                        className="bg-yellow-500"
                        style={{
                          width: `${(stats.filtered_requests / stats.total_requests) * 100}%`,
                        }}
                      />
                      <div
                        className="bg-red-500"
                        style={{
                          width: `${(stats.blocked_requests / stats.total_requests) * 100}%`,
                        }}
                      />
                      <div
                        className="bg-gray-500"
                        style={{
                          width: `${(stats.error_requests / stats.total_requests) * 100}%`,
                        }}
                      />
                    </>
                  )}
                </div>
              </div>
              <div className="flex gap-4 text-sm">
                <div className="flex items-center gap-1">
                  <div className="h-3 w-3 rounded-full bg-green-500" />
                  <span>Allowed</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="h-3 w-3 rounded-full bg-yellow-500" />
                  <span>Filtered</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="h-3 w-3 rounded-full bg-red-500" />
                  <span>Blocked</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="h-3 w-3 rounded-full bg-gray-500" />
                  <span>Error</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
