"use client";

import { useIsAuthenticated, useMsal } from "@azure/msal-react";
import { useGraph } from "@/hooks/use-graph";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { LoginButton } from "@/components/auth/login-button";
import {
  Mail,
  Building2,
  Phone,
  Briefcase,
  MapPin,
  RefreshCw,
  User,
  KeyRound,
  Clock,
  ShieldCheck,
} from "lucide-react";

function ProfileField({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | null | undefined;
}) {
  return (
    <div className="flex items-start gap-3 min-w-0">
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="truncate text-sm font-medium">{value || "Not set"}</p>
      </div>
    </div>
  );
}

function DashboardContent() {
  const { accounts } = useMsal();
  const { graphData, photoUrl, loading, error, refetch } = useGraph();
  const account = accounts[0];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">
            Loading your profile...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-20">
        <Card className="max-w-md">
          <CardContent className="pt-6 text-center">
            <p className="mb-4 text-sm text-destructive">{error}</p>
            <Button onClick={refetch} variant="outline" className="gap-2">
              <RefreshCw className="h-4 w-4" />
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const initials = graphData?.displayName
    ? graphData.displayName
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "U";

  return (
    <div className="grid gap-6 md:grid-cols-3">
      {/* Profile card */}
      <Card className="md:col-span-1">
        <CardHeader className="text-center">
          <Avatar className="mx-auto h-24 w-24">
            {photoUrl && (
              <AvatarImage
                src={photoUrl}
                alt={graphData?.displayName || ""}
              />
            )}
            <AvatarFallback className="bg-primary text-primary-foreground text-2xl">
              {initials}
            </AvatarFallback>
          </Avatar>
          <CardTitle className="mt-4">
            {graphData?.displayName}
          </CardTitle>
          <CardDescription className="truncate px-4">{graphData?.userPrincipalName}</CardDescription>
          {graphData?.jobTitle && (
            <Badge variant="secondary" className="mx-auto mt-2 w-fit">
              {graphData.jobTitle}
            </Badge>
          )}
        </CardHeader>
        <CardContent>
          <Separator className="mb-4" />
          <div className="space-y-4">
            <ProfileField
              icon={Mail}
              label="Email"
              value={graphData?.mail || graphData?.userPrincipalName}
            />
            <ProfileField
              icon={Briefcase}
              label="Job Title"
              value={graphData?.jobTitle}
            />
            <ProfileField
              icon={Building2}
              label="Office Location"
              value={graphData?.officeLocation}
            />
            <ProfileField
              icon={Phone}
              label="Mobile Phone"
              value={graphData?.mobilePhone}
            />
            <ProfileField
              icon={MapPin}
              label="Business Phone"
              value={graphData?.businessPhones?.[0]}
            />
          </div>
        </CardContent>
      </Card>

      {/* Token info */}
      <div className="space-y-6 md:col-span-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <ShieldCheck className="h-5 w-5 text-green-600" />
              Authentication Status
            </CardTitle>
            <CardDescription>
              You are signed in with Microsoft Entra ID
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-lg border p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <User className="h-4 w-4" />
                  Account Name
                </div>
                <p className="mt-1 font-medium">{account?.name}</p>
              </div>
              <div className="rounded-lg border p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Mail className="h-4 w-4" />
                  Username
                </div>
                <p className="mt-1 font-medium">{account?.username}</p>
              </div>
              <div className="rounded-lg border p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <KeyRound className="h-4 w-4" />
                  Tenant ID
                </div>
                <p className="mt-1 font-mono text-xs break-all">
                  {account?.tenantId}
                </p>
              </div>
              <div className="rounded-lg border p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Clock className="h-4 w-4" />
                  Home Account ID
                </div>
                <p className="mt-1 font-mono text-xs break-all">
                  {account?.homeAccountId}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <User className="h-5 w-5 text-blue-600" />
              Microsoft Graph Profile
            </CardTitle>
            <CardDescription>
              Data retrieved from the Graph API (/me endpoint)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="overflow-auto rounded-lg bg-muted p-4 text-xs">
              {JSON.stringify(graphData, null, 2)}
            </pre>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const isAuthenticated = useIsAuthenticated();

  return (
    <div className="container mx-auto max-w-6xl px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Your profile and authentication details
        </p>
      </div>

      {isAuthenticated ? (
        <DashboardContent />
      ) : (
        <Card className="mx-auto max-w-md">
          <CardContent className="flex flex-col items-center gap-4 py-12">
            <ShieldCheck className="h-12 w-12 text-muted-foreground" />
            <div className="text-center">
              <h2 className="text-lg font-semibold">Sign in required</h2>
              <p className="mb-4 text-sm text-muted-foreground">
                Please sign in with your Microsoft account to view your
                dashboard
              </p>
            </div>
            <LoginButton />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
