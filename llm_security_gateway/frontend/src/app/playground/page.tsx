"use client";

import { useState } from "react";
import { Header } from "@/components/shared/header";
import { PromptInput } from "@/components/playground/prompt-input";
import { SecurityResults } from "@/components/playground/security-results";
import { scanText, chatCompletion, type SecurityScanResult } from "@/lib/api";

export default function PlaygroundPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [scanResult, setScanResult] = useState<SecurityScanResult | null>(null);
  const [response, setResponse] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (prompt: string) => {
    setIsLoading(true);
    setError(null);
    setResponse(null);
    setScanResult(null);

    try {
      // First, run security scan
      const result = await scanText(prompt);
      setScanResult(result);

      // If scan passes, try to get LLM response
      if (result.passed) {
        const chatResponse = await chatCompletion([
          { role: "user", content: prompt },
        ]);

        if ("error" in chatResponse && chatResponse.blocked) {
          // Request was blocked by the gateway
          setError(
            (chatResponse.error as { message: string })?.message ||
              "Request blocked by security gateway"
          );
        } else if ("choices" in chatResponse && chatResponse.choices?.[0]?.message?.content) {
          setResponse(chatResponse.choices[0].message.content);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <Header
        title="Security Playground"
        description="Test the security gateway with various prompts"
      />

      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-5xl mx-auto space-y-6">
          <PromptInput onSubmit={handleSubmit} isLoading={isLoading} />
          <SecurityResults result={scanResult} response={response} error={error} />
        </div>
      </div>
    </div>
  );
}
