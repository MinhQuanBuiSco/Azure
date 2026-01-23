"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/shared/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { getAuditLogs, type AuditLog } from "@/lib/api";
import { formatDate, formatDuration } from "@/lib/utils";
import { ChevronLeft, ChevronRight, RefreshCw } from "lucide-react";

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [page, setPage] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 20;

  const fetchLogs = async () => {
    setIsLoading(true);
    try {
      const params: { limit: number; offset: number; status?: string } = {
        limit: pageSize,
        offset: page * pageSize,
      };
      if (statusFilter !== "all") {
        params.status = statusFilter;
      }
      const data = await getAuditLogs(params);
      setLogs(data.logs);
      setTotalCount(data.count);
    } catch (error) {
      console.error("Failed to fetch audit logs:", error);
      setLogs([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [page, statusFilter]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "allowed":
        return <Badge variant="success">Allowed</Badge>;
      case "blocked":
        return <Badge variant="danger">Blocked</Badge>;
      case "filtered":
        return <Badge variant="warning">Filtered</Badge>;
      case "error":
        return <Badge variant="secondary">Error</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  return (
    <div className="flex flex-col h-full">
      <Header
        title="Audit Logs"
        description="View all requests processed by the security gateway"
        actions={
          <div className="flex items-center gap-2">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="allowed">Allowed</SelectItem>
                <SelectItem value="blocked">Blocked</SelectItem>
                <SelectItem value="filtered">Filtered</SelectItem>
                <SelectItem value="error">Error</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="icon" onClick={fetchLogs}>
              <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            </Button>
          </div>
        }
      />

      <div className="flex-1 overflow-auto p-6">
        <Card>
          <CardHeader>
            <CardTitle>Request Logs</CardTitle>
          </CardHeader>
          <CardContent>
            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b text-left text-sm text-gray-500">
                    <th className="pb-3 font-medium">Timestamp</th>
                    <th className="pb-3 font-medium">Endpoint</th>
                    <th className="pb-3 font-medium">Model</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium">Threats</th>
                    <th className="pb-3 font-medium">PII</th>
                    <th className="pb-3 font-medium">Tokens</th>
                    <th className="pb-3 font-medium">Response Time</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="py-8 text-center text-gray-500">
                        {isLoading ? "Loading..." : "No audit logs found"}
                      </td>
                    </tr>
                  ) : (
                    logs.map((log) => (
                      <tr
                        key={log.id}
                        className="border-b last:border-0 hover:bg-gray-50"
                      >
                        <td className="py-3 text-sm">
                          {formatDate(log.timestamp)}
                        </td>
                        <td className="py-3">
                          <code className="text-sm">{log.endpoint}</code>
                        </td>
                        <td className="py-3 text-sm">{log.model || "-"}</td>
                        <td className="py-3">{getStatusBadge(log.status)}</td>
                        <td className="py-3">
                          {log.threats_detected.length > 0 ? (
                            <Badge variant="danger">
                              {log.threats_detected.length}
                            </Badge>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="py-3">
                          {log.pii_detected.length > 0 ? (
                            <Badge variant="warning">
                              {log.pii_detected.length}
                            </Badge>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="py-3 text-sm">
                          {log.total_tokens || "-"}
                        </td>
                        <td className="py-3 text-sm">
                          {log.response_time_ms
                            ? formatDuration(log.response_time_ms)
                            : "-"}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="mt-4 flex items-center justify-between">
              <p className="text-sm text-gray-500">
                Showing {page * pageSize + 1} to{" "}
                {Math.min((page + 1) * pageSize, totalCount || logs.length)} of{" "}
                {totalCount || logs.length} results
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(Math.max(0, page - 1))}
                  disabled={page === 0}
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page + 1)}
                  disabled={logs.length < pageSize}
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
