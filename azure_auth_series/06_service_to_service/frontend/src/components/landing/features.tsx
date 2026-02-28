import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, KeyRound, Network } from "lucide-react";

const features = [
  {
    icon: Users,
    title: "On-Behalf-Of (OBO)",
    description:
      "Task API calls Notification Service as the user. The OBO flow preserves user identity — the downstream service knows exactly who triggered the action.",
    color: "text-violet-600",
    bg: "bg-violet-50",
  },
  {
    icon: KeyRound,
    title: "Client Credentials",
    description:
      "Task API calls Audit Service as itself. No user context needed — the app proves its own identity to log events. Uses application permissions with admin consent.",
    color: "text-blue-600",
    bg: "bg-blue-50",
  },
  {
    icon: Network,
    title: "Microservice Architecture",
    description:
      "Three FastAPI services on different ports. Each validates tokens independently — OBO tokens carry user claims, client credential tokens carry app roles.",
    color: "text-purple-600",
    bg: "bg-purple-50",
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
          Two patterns for service-to-service auth in Azure AD
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
