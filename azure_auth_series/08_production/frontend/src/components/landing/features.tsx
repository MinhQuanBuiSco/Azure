import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart3, Activity, ShieldCheck } from "lucide-react";

const features = [
  {
    icon: BarChart3,
    title: "Application Insights",
    description:
      "Centralized telemetry for APIM and all three microservices. Every request, dependency call, and error flows into a single Application Insights workspace backed by Log Analytics.",
    color: "text-emerald-600",
    bg: "bg-emerald-50",
  },
  {
    icon: Activity,
    title: "OpenTelemetry Instrumentation",
    description:
      "Automatic tracing of FastAPI requests and httpx dependency calls via azure-monitor-opentelemetry. Zero manual span creation — just plug in the connection string and traces flow.",
    color: "text-green-600",
    bg: "bg-green-50",
  },
  {
    icon: ShieldCheck,
    title: "Security Hardening",
    description:
      "Notification and Audit services locked to internal-only ingress. Health probes detect unhealthy instances. Auto-scaling from 1 to 3 replicas handles traffic spikes.",
    color: "text-teal-600",
    bg: "bg-teal-50",
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
          Production monitoring, alerting, and security hardening
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
