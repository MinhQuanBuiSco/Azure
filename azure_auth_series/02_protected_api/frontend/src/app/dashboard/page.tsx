"use client";

import { useState } from "react";
import { useIsAuthenticated, useMsal } from "@azure/msal-react";
import { useApi } from "@/hooks/use-api";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { LoginButton } from "@/components/auth/login-button";
import {
  Mail,
  RefreshCw,
  User,
  KeyRound,
  ShieldCheck,
  Plus,
  Trash2,
  CheckCircle2,
  Circle,
  Server,
} from "lucide-react";

function DashboardContent() {
  const { accounts } = useMsal();
  const { profile, tasks, loading, error, refetch, addTask, toggleTask, removeTask } =
    useApi();
  const account = accounts[0];
  const [newTaskTitle, setNewTaskTitle] = useState("");

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">
            Loading from protected API...
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

  const initials = profile?.name
    ? profile.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "U";

  const handleAddTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;
    await addTask(newTaskTitle.trim());
    setNewTaskTitle("");
  };

  return (
    <div className="grid gap-6 md:grid-cols-3">
      {/* Profile card */}
      <Card className="md:col-span-1">
        <CardHeader className="text-center">
          <Avatar className="mx-auto h-24 w-24">
            <AvatarFallback className="bg-primary text-primary-foreground text-2xl">
              {initials}
            </AvatarFallback>
          </Avatar>
          <CardTitle className="mt-4">{profile?.name}</CardTitle>
          <CardDescription className="truncate px-4">
            {profile?.email}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Separator className="mb-4" />
          <div className="space-y-4">
            <div className="flex items-start gap-3 min-w-0">
              <Mail className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground">Email</p>
                <p className="truncate text-sm font-medium">
                  {profile?.email || "Not set"}
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3 min-w-0">
              <KeyRound className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground">Scopes Granted</p>
                <p className="truncate text-sm font-medium">
                  {profile?.scopes || "None"}
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3 min-w-0">
              <Server className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground">Data Source</p>
                <p className="text-sm font-medium">Protected API</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Right column */}
      <div className="space-y-6 md:col-span-2">
        {/* Auth status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <ShieldCheck className="h-5 w-5 text-green-600" />
              Authentication Status
            </CardTitle>
            <CardDescription>
              Token validated by our FastAPI backend
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
                  {profile?.tenant_id}
                </p>
              </div>
              <div className="rounded-lg border p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Server className="h-4 w-4" />
                  User Object ID
                </div>
                <p className="mt-1 font-mono text-xs break-all">
                  {profile?.id}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tasks */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <CheckCircle2 className="h-5 w-5 text-blue-600" />
              My Tasks
            </CardTitle>
            <CardDescription>
              Stored on the backend — CRUD via protected API endpoints
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAddTask} className="flex gap-2 mb-4">
              <input
                type="text"
                value={newTaskTitle}
                onChange={(e) => setNewTaskTitle(e.target.value)}
                placeholder="Add a new task..."
                className="flex-1 rounded-md border bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
              <Button type="submit" size="sm" className="gap-1">
                <Plus className="h-4 w-4" />
                Add
              </Button>
            </form>

            {tasks.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">
                No tasks yet. Add one above!
              </p>
            ) : (
              <div className="space-y-2">
                {tasks.map((task) => (
                  <div
                    key={task.id}
                    className="flex items-center gap-3 rounded-lg border p-3"
                  >
                    <button
                      onClick={() => toggleTask(task.id, !task.completed)}
                      className="shrink-0 text-muted-foreground hover:text-primary"
                    >
                      {task.completed ? (
                        <CheckCircle2 className="h-5 w-5 text-green-600" />
                      ) : (
                        <Circle className="h-5 w-5" />
                      )}
                    </button>
                    <span
                      className={`flex-1 text-sm ${
                        task.completed
                          ? "text-muted-foreground line-through"
                          : ""
                      }`}
                    >
                      {task.title}
                    </span>
                    <button
                      onClick={() => removeTask(task.id)}
                      className="shrink-0 text-muted-foreground hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
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
          Your profile and tasks from the protected API
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
