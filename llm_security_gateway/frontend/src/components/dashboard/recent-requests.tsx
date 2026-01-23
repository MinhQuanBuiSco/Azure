"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatDate, formatDuration } from "@/lib/utils";
import type { AuditLog } from "@/lib/api";

interface RecentRequestsProps {
  logs: AuditLog[];
}

export function RecentRequests({ logs }: RecentRequestsProps) {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "allowed":
        return <Badge variant="success">Allowed</Badge>;
      case "blocked":
        return <Badge variant="danger">Blocked</Badge>;
      case "filtered":
        return <Badge variant="warning">Filtered</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Requests</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {logs.length === 0 ? (
            <p className="text-center text-gray-500 py-8">No recent requests</p>
          ) : (
            logs.map((log) => (
              <div
                key={log.id}
                className="flex items-center justify-between border-b pb-4 last:border-0 last:pb-0"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm">{log.endpoint}</span>
                    {getStatusBadge(log.status)}
                  </div>
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span>{formatDate(log.timestamp)}</span>
                    {log.model && <span>Model: {log.model}</span>}
                    {log.response_time_ms && (
                      <span>{formatDuration(log.response_time_ms)}</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {log.threats_detected.length > 0 && (
                    <Badge variant="danger">
                      {log.threats_detected.length} threats
                    </Badge>
                  )}
                  {log.pii_detected.length > 0 && (
                    <Badge variant="warning">
                      {log.pii_detected.length} PII
                    </Badge>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
