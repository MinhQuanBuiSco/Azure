import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { KeyRound, ShieldCheck, Network } from "lucide-react";

const features = [
  {
    icon: KeyRound,
    title: "Enterprise SSO",
    description:
      "Sign in with any Microsoft work, school, or personal account. Seamless single sign-on powered by Microsoft Entra ID.",
    color: "text-blue-600",
    bg: "bg-blue-50",
  },
  {
    icon: ShieldCheck,
    title: "Secure by Default",
    description:
      "Industry-standard OAuth 2.0 and OpenID Connect protocols. Token-based authentication with automatic refresh.",
    color: "text-green-600",
    bg: "bg-green-50",
  },
  {
    icon: Network,
    title: "Graph Integration",
    description:
      "Access user profiles, photos, and organizational data through the Microsoft Graph API with proper scopes.",
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
          This demo covers the essential building blocks of Azure authentication
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
