"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import type { SecurityScanResult } from "@/lib/api";
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  User,
  Key,
  Clock,
} from "lucide-react";

interface SecurityResultsProps {
  result: SecurityScanResult | null;
  response?: string | null;
  error?: string | null;
}

export function SecurityResults({ result, response, error }: SecurityResultsProps) {
  if (!result && !error) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-gray-500">
          <ShieldCheck className="mx-auto h-12 w-12 text-gray-300" />
          <p className="mt-4">Run a security test to see results</p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-6">
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (!result) return null;

  const getActionBadge = () => {
    switch (result.action) {
      case "allow":
        return <Badge variant="success">Allowed</Badge>;
      case "block":
        return <Badge variant="danger">Blocked</Badge>;
      case "filter":
        return <Badge variant="warning">Filtered</Badge>;
      case "warn":
        return <Badge variant="warning">Warning</Badge>;
      default:
        return <Badge>{result.action}</Badge>;
    }
  };

  const getRiskColor = (score: number) => {
    if (score >= 0.8) return "bg-red-500";
    if (score >= 0.5) return "bg-orange-500";
    if (score >= 0.3) return "bg-yellow-500";
    return "bg-green-500";
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            {result.passed ? (
              <ShieldCheck className="h-5 w-5 text-green-600" />
            ) : (
              <ShieldAlert className="h-5 w-5 text-red-600" />
            )}
            Security Scan Results
          </CardTitle>
          {getActionBadge()}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="space-y-1">
            <p className="text-sm text-gray-500">Overall Risk</p>
            <div className="flex items-center gap-2">
              <Progress
                value={result.overall_risk_score * 100}
                className={`h-2 ${getRiskColor(result.overall_risk_score)}`}
              />
              <span className="text-sm font-medium">
                {(result.overall_risk_score * 100).toFixed(0)}%
              </span>
            </div>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-gray-500">Injection Score</p>
            <div className="flex items-center gap-2">
              <Progress
                value={result.prompt_injection_score * 100}
                className="h-2"
              />
              <span className="text-sm font-medium">
                {(result.prompt_injection_score * 100).toFixed(0)}%
              </span>
            </div>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-gray-500">Jailbreak Score</p>
            <div className="flex items-center gap-2">
              <Progress value={result.jailbreak_score * 100} className="h-2" />
              <span className="text-sm font-medium">
                {(result.jailbreak_score * 100).toFixed(0)}%
              </span>
            </div>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-gray-500">Scan Time</p>
            <p className="text-sm font-medium flex items-center gap-1">
              <Clock className="h-4 w-4" />
              {result.scan_duration_ms?.toFixed(0) || 0}ms
            </p>
          </div>
        </div>

        {/* Action Reason */}
        {result.action_reason && (
          <Alert variant={result.passed ? "default" : "destructive"}>
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Action Reason</AlertTitle>
            <AlertDescription>{result.action_reason}</AlertDescription>
          </Alert>
        )}

        {/* Threats */}
        {result.threats.length > 0 && (
          <div className="space-y-2">
            <h4 className="flex items-center gap-2 font-medium">
              <ShieldAlert className="h-4 w-4 text-red-600" />
              Threats Detected ({result.threats.length})
            </h4>
            <div className="space-y-2">
              {result.threats.map((threat, i) => (
                <div
                  key={i}
                  className="rounded-lg border border-red-200 bg-red-50 p-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-red-800">
                      {threat.type.replace("_", " ")}
                    </span>
                    <Badge
                      variant={
                        threat.severity === "critical" || threat.severity === "high"
                          ? "danger"
                          : "warning"
                      }
                    >
                      {threat.severity}
                    </Badge>
                  </div>
                  <p className="mt-1 text-sm text-red-700">{threat.description}</p>
                  {threat.matched_pattern && (
                    <p className="mt-1 font-mono text-xs text-red-600">
                      Match: {threat.matched_pattern}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* PII Detections */}
        {result.pii_detections.length > 0 && (
          <div className="space-y-2">
            <h4 className="flex items-center gap-2 font-medium">
              <User className="h-4 w-4 text-blue-600" />
              PII Detected ({result.pii_detections.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {result.pii_detections.map((pii, i) => (
                <div
                  key={i}
                  className="rounded-lg border border-blue-200 bg-blue-50 px-3 py-2"
                >
                  <span className="font-medium text-blue-800">
                    {pii.entity_type}
                  </span>
                  <span className="ml-2 font-mono text-sm text-blue-600">
                    {pii.text} → {pii.masked_text}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Secret Detections */}
        {result.secret_detections.length > 0 && (
          <div className="space-y-2">
            <h4 className="flex items-center gap-2 font-medium">
              <Key className="h-4 w-4 text-purple-600" />
              Secrets Detected ({result.secret_detections.length})
            </h4>
            <div className="space-y-2">
              {result.secret_detections.map((secret, i) => (
                <div
                  key={i}
                  className="rounded-lg border border-purple-200 bg-purple-50 p-3"
                >
                  <span className="font-medium text-purple-800">
                    {secret.type.replace("_", " ")}
                  </span>
                  <p className="text-sm text-purple-700">{secret.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Transformations */}
        {result.transformations.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-medium">Transformations Applied</h4>
            <div className="flex flex-wrap gap-2">
              {result.transformations.map((t, i) => (
                <Badge key={i} variant="secondary">
                  {t.replace("_", " ")}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Response (if any) */}
        {response && (
          <div className="space-y-2">
            <h4 className="font-medium">LLM Response</h4>
            <div className="rounded-lg border bg-gray-50 p-4">
              <p className="whitespace-pre-wrap text-sm">{response}</p>
            </div>
          </div>
        )}

        {/* All Clear */}
        {result.passed &&
          result.threats.length === 0 &&
          result.pii_detections.length === 0 &&
          result.secret_detections.length === 0 && (
            <Alert variant="success">
              <ShieldCheck className="h-4 w-4" />
              <AlertTitle>All Clear</AlertTitle>
              <AlertDescription>
                No security threats, PII, or secrets detected in this prompt.
              </AlertDescription>
            </Alert>
          )}
      </CardContent>
    </Card>
  );
}
