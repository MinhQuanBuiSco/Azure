import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Shield, Gauge, Network } from "lucide-react";

const features = [
  {
    icon: Shield,
    title: "Centralized JWT Validation",
    description:
      "APIM validates every token at the gateway using OpenID Connect discovery. Backends receive pre-validated claims as headers — no more duplicated auth logic across services.",
    color: "text-blue-600",
    bg: "bg-blue-50",
  },
  {
    icon: Gauge,
    title: "Rate Limiting",
    description:
      "Per-user rate limiting via JWT subject claim with IP-based fallback. APIM returns HTTP 429 when limits are exceeded — protecting your backends without any application code.",
    color: "text-indigo-600",
    bg: "bg-indigo-50",
  },
  {
    icon: Network,
    title: "Multi-Service Routing",
    description:
      "Single APIM entry point routes to three Container Apps: Task API, Notification, and Audit. Each API has its own policy with different JWT audiences and validation rules.",
    color: "text-sky-600",
    bg: "bg-sky-50",
  },
];

export function Features() {
  return (
    <section className="container mx-auto max-w-6xl px-4 py-20">
      <div className="mb-12 text-center">
        <h2 className="mb-4 text-3xl font-bold tracking-tight">
          What you&apos;ll learn
        </h2>
        <p className="text-muted-foreground md:text-lg">
          Centralized auth management with Azure API Management
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {features.map((feature) => (
          <Card
            key={feature.title}
            className="border-0 shadow-md transition-shadow hover:shadow-lg"
          >
            <CardHeader>
              <div
                className={`mb-2 inline-flex h-12 w-12 items-center justify-center rounded-lg ${feature.bg}`}
              >
                <feature.icon className={`h-6 w-6 ${feature.color}`} />
              </div>
              <CardTitle className="text-xl">{feature.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">{feature.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}
