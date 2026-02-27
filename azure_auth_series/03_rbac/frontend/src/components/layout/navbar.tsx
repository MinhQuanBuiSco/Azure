"use client";

import { useState } from "react";
import Link from "next/link";
import { useIsAuthenticated } from "@azure/msal-react";
import { LoginButton } from "@/components/auth/login-button";
import { UserProfile } from "@/components/auth/user-profile";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Menu, Shield } from "lucide-react";

export function Navbar() {
  const isAuthenticated = useIsAuthenticated();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between px-4 mx-auto max-w-6xl">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <Shield className="h-6 w-6 text-blue-600" />
          <span className="text-lg">Azure Auth</span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-6">
          <Link
            href="/"
            className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            Home
          </Link>
          {isAuthenticated && (
            <Link
              href="/dashboard"
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              Dashboard
            </Link>
          )}
          {isAuthenticated ? <UserProfile /> : <LoginButton />}
        </nav>

        {/* Mobile nav */}
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger asChild className="md:hidden">
            <Button variant="ghost" size="icon">
              <Menu className="h-5 w-5" />
              <span className="sr-only">Toggle menu</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="w-72">
            <nav className="flex flex-col gap-4 mt-8">
              <Link
                href="/"
                onClick={() => setOpen(false)}
                className="text-sm font-medium transition-colors hover:text-foreground"
              >
                Home
              </Link>
              {isAuthenticated && (
                <Link
                  href="/dashboard"
                  onClick={() => setOpen(false)}
                  className="text-sm font-medium transition-colors hover:text-foreground"
                >
                  Dashboard
                </Link>
              )}
              <div className="pt-4">
                {isAuthenticated ? <UserProfile /> : <LoginButton />}
              </div>
            </nav>
          </SheetContent>
        </Sheet>
      </div>
    </header>
  );
}
