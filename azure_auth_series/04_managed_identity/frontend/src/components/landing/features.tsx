import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Shield, Users, Lock } from "lucide-react";

const features = [
  {
    icon: Shield,
    title: "App Roles",
    description:
      "Define Admin, Editor, and Reader roles directly in Azure AD. Roles are included in the JWT token as claims — no database needed.",
    color: "text-red-600",
    bg: "bg-red-50",
  },
  {
    icon: Users,
    title: "Per-Role Permissions",
    description:
      "Admin gets full CRUD on all tasks. Editor can create and manage their own. Reader has read-only access. All enforced server-side.",
    color: "text-blue-600",
    bg: "bg-blue-50",
  },
  {
    icon: Lock,
    title: "Adaptive UI",
    description:
      "The frontend adapts based on your role — buttons, forms, and views change automatically. Try signing in as different users to see it.",
    color: "text-green-600",
    bg: "bg-green-50",
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
          This demo covers role-based access control with Azure AD App Roles
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
