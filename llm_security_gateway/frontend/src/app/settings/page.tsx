"use client";

import { useState, useEffect } from "react";
import { Header } from "@/components/shared/header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { healthCheck } from "@/lib/api";
import {
  CheckCircle,
  XCircle,
  RefreshCw,
  Shield,
  Database,
  Cpu,
  Globe,
} from "lucide-react";

export default function SettingsPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [healthStatus, setHealthStatus] = useState<{
    status: string;
    version: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await healthCheck();
      setHealthStatus(result);
    } catch (err) {
      setError("Unable to connect to backend");
      setHealthStatus(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  const features = [
    {
      name: "Prompt Injection Detection",
      description: "Detects attempts to override system instructions",
      enabled: true,
      icon: Shield,
    },
    {
      name: "Jailbreak Detection",
      description: "Identifies known jailbreak patterns and attacks",
      enabled: true,
      icon: Shield,
    },
    {
      name: "PII Detection & Masking",
      description: "Detects and masks personal identifiable information",
      enabled: true,
      icon: Shield,
    },
    {
      name: "Secret Scanning",
      description: "Identifies API keys, tokens, and credentials",
      enabled: true,
      icon: Shield,
    },
    {
      name: "Content Filtering",
      description: "Enforces content policies and safety guidelines",
      enabled: true,
      icon: Shield,
    },
    {
      name: "Rate Limiting",
      description: "Prevents abuse with configurable rate limits",
      enabled: true,
      icon: Globe,
    },
  ];

  return (
    <div className="flex flex-col h-full">
      <Header
        title="Settings"
        description="Configure your LLM Security Gateway"
      />

      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Health Status */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>System Status</CardTitle>
                  <CardDescription>
                    Check the health of the backend services
                  </CardDescription>
                </div>
                <Button variant="outline" onClick={checkHealth}>
                  <RefreshCw
                    className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`}
                  />
                  Refresh
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {error ? (
                <Alert variant="destructive">
                  <XCircle className="h-4 w-4" />
                  <AlertTitle>Connection Error</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              ) : healthStatus ? (
                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span className="font-medium">Backend</span>
                    <Badge variant="success">{healthStatus.status}</Badge>
                  </div>
                  <div className="text-sm text-gray-500">
                    Version: {healthStatus.version}
                  </div>
                </div>
              ) : (
                <div className="text-gray-500">Checking...</div>
              )}
            </CardContent>
          </Card>

          {/* Security Features */}
          <Card>
            <CardHeader>
              <CardTitle>Security Features</CardTitle>
              <CardDescription>
                Configure which security features are enabled
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {features.map((feature) => (
                  <div
                    key={feature.name}
                    className="flex items-center justify-between p-4 rounded-lg border"
                  >
                    <div className="flex items-center gap-4">
                      <div className="p-2 bg-blue-100 rounded-lg">
                        <feature.icon className="h-5 w-5 text-blue-600" />
                      </div>
                      <div>
                        <h4 className="font-medium">{feature.name}</h4>
                        <p className="text-sm text-gray-500">
                          {feature.description}
                        </p>
                      </div>
                    </div>
                    <Badge variant={feature.enabled ? "success" : "secondary"}>
                      {feature.enabled ? "Enabled" : "Disabled"}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>Configuration</CardTitle>
              <CardDescription>
                Current gateway configuration (read-only)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="p-4 rounded-lg bg-gray-50">
                  <div className="flex items-center gap-2 mb-2">
                    <Cpu className="h-4 w-4 text-gray-500" />
                    <span className="text-sm font-medium">LLM Provider</span>
                  </div>
                  <p className="text-sm text-gray-600">Azure AI Foundry</p>
                  <p className="text-xs text-gray-400 mt-1">GPT-4o, GPT-4o-mini</p>
                </div>
                <div className="p-4 rounded-lg bg-gray-50">
                  <div className="flex items-center gap-2 mb-2">
                    <Database className="h-4 w-4 text-gray-500" />
                    <span className="text-sm font-medium">Audit Storage</span>
                  </div>
                  <p className="text-sm text-gray-600">Azure Cosmos DB</p>
                  <p className="text-xs text-gray-400 mt-1">Serverless mode</p>
                </div>
                <div className="p-4 rounded-lg bg-gray-50">
                  <div className="flex items-center gap-2 mb-2">
                    <Globe className="h-4 w-4 text-gray-500" />
                    <span className="text-sm font-medium">Rate Limiting</span>
                  </div>
                  <p className="text-sm text-gray-600">Azure Redis Cache</p>
                  <p className="text-xs text-gray-400 mt-1">
                    100 requests / 60 seconds
                  </p>
                </div>
                <div className="p-4 rounded-lg bg-gray-50">
                  <div className="flex items-center gap-2 mb-2">
                    <Shield className="h-4 w-4 text-gray-500" />
                    <span className="text-sm font-medium">Content Safety</span>
                  </div>
                  <p className="text-sm text-gray-600">Azure AI Content Safety</p>
                  <p className="text-xs text-gray-400 mt-1">Prompt Shields enabled</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* API Information */}
          <Card>
            <CardHeader>
              <CardTitle>API Information</CardTitle>
              <CardDescription>Use these endpoints to integrate with the gateway</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="p-3 rounded-lg bg-gray-50 font-mono text-sm">
                  <span className="text-green-600 font-medium">POST</span>{" "}
                  /v1/chat/completions
                  <p className="text-xs text-gray-500 mt-1">
                    OpenAI-compatible chat completions with security scanning
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-gray-50 font-mono text-sm">
                  <span className="text-green-600 font-medium">POST</span>{" "}
                  /v1/completions
                  <p className="text-xs text-gray-500 mt-1">
                    OpenAI-compatible text completions with security scanning
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-gray-50 font-mono text-sm">
                  <span className="text-blue-600 font-medium">POST</span>{" "}
                  /v1/security/scan
                  <p className="text-xs text-gray-500 mt-1">
                    Standalone security scan endpoint for testing
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-gray-50 font-mono text-sm">
                  <span className="text-purple-600 font-medium">GET</span>{" "}
                  /api/audit
                  <p className="text-xs text-gray-500 mt-1">
                    Query audit logs with filtering
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
