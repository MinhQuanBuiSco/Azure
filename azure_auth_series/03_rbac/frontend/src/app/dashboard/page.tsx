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
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { LoginButton } from "@/components/auth/login-button";
import {
  Mail,
  RefreshCw,
  User,
  KeyRound,
  ShieldCheck,
  ShieldAlert,
  Plus,
  Trash2,
  CheckCircle2,
  Circle,
  Shield,
} from "lucide-react";

const ROLE_CONFIG: Record<string, { color: string; bg: string; description: string }> = {
  Admin: {
    color: "text-red-700",
    bg: "bg-red-100 border-red-200",
    description: "Full access — manage all tasks and users",
  },
  Editor: {
    color: "text-blue-700",
    bg: "bg-blue-100 border-blue-200",
    description: "Create, read, and update your own tasks",
  },
  Reader: {
    color: "text-green-700",
    bg: "bg-green-100 border-green-200",
    description: "Read-only access to your own tasks",
  },
};

function DashboardContent() {
  const { accounts } = useMsal();
  const {
    profile,
    tasks,
    loading,
    error,
    refetch,
    addTask,
    toggleTask,
    removeTask,
  } = useApi();
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

  const roles = profile?.roles || [];
  const primaryRole = roles[0] || "No Role";
  const roleConfig = ROLE_CONFIG[primaryRole];

  const isAdmin = roles.includes("Admin");
  const isEditor = roles.includes("Editor");
  const canCreate = isAdmin || isEditor;
  const canEdit = isAdmin || isEditor;
  const canDelete = isAdmin;

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
          {/* Role badge */}
          <div className="flex justify-center pt-2">
            {roles.map((role) => {
              const rc = ROLE_CONFIG[role];
              return (
                <Badge
                  key={role}
                  variant="outline"
                  className={`${rc?.bg || ""} ${rc?.color || ""} border`}
                >
                  <Shield className="mr-1 h-3 w-3" />
                  {role}
                </Badge>
              );
            })}
          </div>
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
              <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground">Permissions</p>
                <p className="text-sm font-medium">
                  {roleConfig?.description || "No role assigned"}
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3 min-w-0">
              <KeyRound className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground">Scopes</p>
                <p className="truncate text-sm font-medium">
                  {profile?.scopes || "None"}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Right column */}
      <div className="space-y-6 md:col-span-2">
        {/* Role info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <ShieldCheck className="h-5 w-5 text-green-600" />
              RBAC Status
            </CardTitle>
            <CardDescription>
              Role-based access control via Azure AD App Roles
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-lg border p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <User className="h-4 w-4" />
                  Account
                </div>
                <p className="mt-1 font-medium">{account?.name}</p>
              </div>
              <div className="rounded-lg border p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Shield className="h-4 w-4" />
                  Assigned Role
                </div>
                <div className="mt-1 flex gap-1">
                  {roles.map((role) => {
                    const rc = ROLE_CONFIG[role];
                    return (
                      <span
                        key={role}
                        className={`rounded px-2 py-0.5 text-sm font-semibold ${rc?.bg || ""} ${rc?.color || ""}`}
                      >
                        {role}
                      </span>
                    );
                  })}
                </div>
              </div>
              <div className="rounded-lg border p-4 sm:col-span-2">
                <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
                  <KeyRound className="h-4 w-4" />
                  Your Permissions
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge variant={canCreate ? "default" : "secondary"}>
                    {canCreate ? "✓" : "✗"} Create Tasks
                  </Badge>
                  <Badge variant="default">✓ Read Tasks</Badge>
                  <Badge variant={canEdit ? "default" : "secondary"}>
                    {canEdit ? "✓" : "✗"} Edit Tasks
                  </Badge>
                  <Badge variant={canDelete ? "default" : "secondary"}>
                    {canDelete ? "✓" : "✗"} Delete Tasks
                  </Badge>
                  <Badge variant={isAdmin ? "default" : "secondary"}>
                    {isAdmin ? "✓" : "✗"} View All Users
                  </Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tasks */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <CheckCircle2 className="h-5 w-5 text-blue-600" />
              {isAdmin ? "All Tasks" : "My Tasks"}
            </CardTitle>
            <CardDescription>
              {isAdmin
                ? "Admin view — showing tasks from all users"
                : canCreate
                  ? "Create and manage your own tasks"
                  : "Read-only view of your tasks"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {canCreate && (
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
            )}

            {tasks.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">
                {canCreate
                  ? "No tasks yet. Add one above!"
                  : "No tasks to display."}
              </p>
            ) : (
              <div className="space-y-2">
                {tasks.map((task) => (
                  <div
                    key={task.id}
                    className="flex items-center gap-3 rounded-lg border p-3"
                  >
                    {canEdit ? (
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
                    ) : (
                      <span className="shrink-0">
                        {task.completed ? (
                          <CheckCircle2 className="h-5 w-5 text-green-600" />
                        ) : (
                          <Circle className="h-5 w-5 text-muted-foreground" />
                        )}
                      </span>
                    )}
                    <span
                      className={`flex-1 text-sm ${
                        task.completed
                          ? "text-muted-foreground line-through"
                          : ""
                      }`}
                    >
                      {task.title}
                    </span>
                    {isAdmin && task.owner_name && (
                      <Badge variant="outline" className="text-xs">
                        {task.owner_name}
                      </Badge>
                    )}
                    {canDelete && (
                      <button
                        onClick={() => removeTask(task.id)}
                        className="shrink-0 text-muted-foreground hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
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
          Role-based access control with Azure AD App Roles
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
