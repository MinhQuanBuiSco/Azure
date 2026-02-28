"use client";

import Link from "next/link";
import { useIsAuthenticated } from "@azure/msal-react";
import { useMsal } from "@azure/msal-react";
import { apiLoginRequest } from "@/config/auth-config";
import { Button } from "@/components/ui/button";
import { ArrowRight, LogIn, Shield, Gauge, Network } from "lucide-react";

export function Hero() {
  const isAuthenticated = useIsAuthenticated();
  const { instance } = useMsal();

  const handleLogin = () => {
    instance.loginPopup(apiLoginRequest);
  };

  return (
    <section className="relative overflow-hidden">
      {/* Background gradient — blue/indigo theme */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-indigo-50 to-sky-50" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-blue-100/40 via-transparent to-transparent" />

      {/* Decorative elements */}
      <div className="absolute top-20 left-10 h-72 w-72 rounded-full bg-blue-200/20 blur-3xl" />
      <div className="absolute bottom-10 right-10 h-96 w-96 rounded-full bg-indigo-200/20 blur-3xl" />

      <div className="relative container mx-auto max-w-6xl px-4 py-24 md:py-32 lg:py-40">
        <div className="mx-auto max-w-3xl text-center">
          {/* Badge */}
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border bg-white/80 px-4 py-1.5 text-sm font-medium text-blue-700 shadow-sm backdrop-blur">
            <Shield className="h-4 w-4" />
            Azure Auth Series &mdash; Blog 7
          </div>

          {/* Heading */}
          <h1 className="mb-6 text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl md:text-6xl">
            API Gateway{" "}
            <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              Authentication
            </span>
          </h1>

          {/* Description */}
          <p className="mb-10 text-lg text-muted-foreground md:text-xl">
            Centralize JWT validation, rate limiting, and routing with Azure API
            Management &mdash; one gateway protecting three microservices in the
            cloud.
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
              <Shield className="h-4 w-4 text-blue-600" />
              Centralized JWT Validation
            </div>
            <div className="flex items-center gap-2">
              <Gauge className="h-4 w-4 text-indigo-600" />
              Rate Limiting
            </div>
            <div className="flex items-center gap-2">
              <Network className="h-4 w-4 text-sky-600" />
              Multi-Service Routing
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
