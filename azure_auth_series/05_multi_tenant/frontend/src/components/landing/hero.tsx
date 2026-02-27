"use client";

import Link from "next/link";
import { useIsAuthenticated } from "@azure/msal-react";
import { useMsal } from "@azure/msal-react";
import { apiLoginRequest } from "@/config/auth-config";
import { Button } from "@/components/ui/button";
import { ArrowRight, LogIn, Shield, Lock, Building2 } from "lucide-react";

export function Hero() {
  const isAuthenticated = useIsAuthenticated();
  const { instance } = useMsal();

  const handleLogin = () => {
    instance.loginPopup(apiLoginRequest);
  };

  return (
    <section className="relative overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-emerald-100/40 via-transparent to-transparent" />

      {/* Decorative elements */}
      <div className="absolute top-20 left-10 h-72 w-72 rounded-full bg-emerald-200/20 blur-3xl" />
      <div className="absolute bottom-10 right-10 h-96 w-96 rounded-full bg-cyan-200/20 blur-3xl" />

      <div className="relative container mx-auto max-w-6xl px-4 py-24 md:py-32 lg:py-40">
        <div className="mx-auto max-w-3xl text-center">
          {/* Badge */}
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border bg-white/80 px-4 py-1.5 text-sm font-medium text-emerald-700 shadow-sm backdrop-blur">
            <Building2 className="h-4 w-4" />
            Azure Auth Series &mdash; Blog 5
          </div>

          {/* Heading */}
          <h1 className="mb-6 text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl md:text-6xl">
            Go multi-tenant with{" "}
            <span className="bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
              tenant-isolated data
            </span>
          </h1>

          {/* Description */}
          <p className="mb-10 text-lg text-muted-foreground md:text-xl">
            Users from any Azure AD organization can sign in. Each tenant gets
            isolated data, dynamic JWKS validation, and a configurable
            allow-list &mdash; all running locally.
          </p>

          {/* CTA */}
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            {isAuthenticated ? (
              <Button asChild size="lg" className="gap-2 text-base">
                <Link href="/dashboard">
                  Go to Dashboard
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
            ) : (
              <Button
                onClick={handleLogin}
                size="lg"
                className="gap-2 text-base"
              >
                <LogIn className="h-4 w-4" />
                Sign in with Microsoft
              </Button>
            )}
          </div>

          {/* Trust indicators */}
          <div className="mt-16 flex flex-wrap items-center justify-center gap-8 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <Lock className="h-4 w-4 text-green-600" />
              OAuth 2.0 / OpenID Connect
            </div>
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-blue-600" />
              Microsoft Entra ID
            </div>
            <div className="flex items-center gap-2">
              <Building2 className="h-4 w-4 text-emerald-600" />
              Multi-Tenant / Any Azure AD Org
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
