import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Server, ShieldCheck, KeyRound } from "lucide-react";

const features = [
  {
    icon: Server,
    title: "Protected API",
    description:
      "A FastAPI backend that validates Azure AD JWT tokens on every request. Only authenticated users can access the endpoints.",
    color: "text-blue-600",
    bg: "bg-blue-50",
  },
  {
    icon: ShieldCheck,
    title: "JWT Validation",
    description:
      "Tokens are verified against Microsoft's JWKS endpoint — checking signature, audience, issuer, and expiration automatically.",
    color: "text-green-600",
    bg: "bg-green-50",
  },
  {
    icon: KeyRound,
    title: "Custom API Scopes",
    description:
      "The API exposes its own OAuth scope (access_as_user). The frontend requests this scope and passes the token to the backend.",
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
          This demo covers building and securing a backend API with Azure AD
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
