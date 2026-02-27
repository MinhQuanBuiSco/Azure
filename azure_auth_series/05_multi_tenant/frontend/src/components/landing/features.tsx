import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Building2, Shield, Lock } from "lucide-react";

const features = [
  {
    icon: Building2,
    title: "Multi-Tenant Auth",
    description:
      "Any Azure AD organization can sign in. The backend dynamically resolves JWKS endpoints and issuers per tenant — no hardcoded tenant IDs in validation.",
    color: "text-emerald-600",
    bg: "bg-emerald-50",
  },
  {
    icon: Shield,
    title: "Tenant Allow-List",
    description:
      "Control which organizations can access your app. Add tenant IDs to the allow-list, or set ALLOW_ANY_TENANT=true to go fully open.",
    color: "text-blue-600",
    bg: "bg-blue-50",
  },
  {
    icon: Lock,
    title: "Tenant-Isolated Data",
    description:
      "Each tenant's tasks are completely isolated. Admins see all tasks in their organization only — never across tenant boundaries.",
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
          This demo covers multi-tenant authentication with tenant isolation
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
