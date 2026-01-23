"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { examplePrompts, type ExamplePrompt } from "@/lib/examples";
import { ShieldAlert, User, Key, AlertTriangle, CheckCircle } from "lucide-react";

interface PromptInputProps {
  onSubmit: (prompt: string) => void;
  isLoading: boolean;
}

export function PromptInput({ onSubmit, isLoading }: PromptInputProps) {
  const [prompt, setPrompt] = useState("");

  const handleExampleClick = (example: ExamplePrompt) => {
    setPrompt(example.prompt);
  };

  const handleSubmit = () => {
    if (prompt.trim()) {
      onSubmit(prompt);
    }
  };

  const categoryIcons = {
    injection: ShieldAlert,
    jailbreak: AlertTriangle,
    pii: User,
    secrets: Key,
    benign: CheckCircle,
  };

  const categoryColors = {
    injection: "text-red-600",
    jailbreak: "text-orange-600",
    pii: "text-blue-600",
    secrets: "text-purple-600",
    benign: "text-green-600",
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Security Testing Playground</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Example Prompts */}
        <Tabs defaultValue="injection" className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="injection">Injection</TabsTrigger>
            <TabsTrigger value="jailbreak">Jailbreak</TabsTrigger>
            <TabsTrigger value="pii">PII</TabsTrigger>
            <TabsTrigger value="secrets">Secrets</TabsTrigger>
            <TabsTrigger value="benign">Benign</TabsTrigger>
          </TabsList>
          {(["injection", "jailbreak", "pii", "secrets", "benign"] as const).map(
            (category) => {
              const Icon = categoryIcons[category];
              const color = categoryColors[category];
              const examples = examplePrompts.filter(
                (p) => p.category === category
              );

              return (
                <TabsContent key={category} value={category}>
                  <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                    {examples.map((example) => (
                      <Button
                        key={example.id}
                        variant="outline"
                        className="h-auto flex-col items-start p-3 text-left"
                        onClick={() => handleExampleClick(example)}
                      >
                        <div className="flex items-center gap-2">
                          <Icon className={`h-4 w-4 ${color}`} />
                          <span className="font-medium">{example.name}</span>
                        </div>
                        <span className="mt-1 text-xs text-gray-500">
                          {example.description}
                        </span>
                      </Button>
                    ))}
                  </div>
                </TabsContent>
              );
            }
          )}
        </Tabs>

        {/* Prompt Input */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Prompt</label>
          <Textarea
            placeholder="Enter a prompt to test the security gateway..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="min-h-[150px] font-mono text-sm"
          />
        </div>

        {/* Submit Button */}
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => setPrompt("")}>
            Clear
          </Button>
          <Button onClick={handleSubmit} disabled={isLoading || !prompt.trim()}>
            {isLoading ? "Scanning..." : "Test Security"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
