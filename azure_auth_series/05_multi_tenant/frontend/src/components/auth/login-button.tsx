"use client";

import { useMsal } from "@azure/msal-react";
import { apiLoginRequest } from "@/config/auth-config";
import { Button } from "@/components/ui/button";
import { LogIn } from "lucide-react";

export function LoginButton() {
  const { instance } = useMsal();

  const handleLogin = () => {
    instance.loginPopup(apiLoginRequest);
  };

  return (
    <Button onClick={handleLogin} className="gap-2">
      <LogIn className="h-4 w-4" />
      Sign in with Microsoft
    </Button>
  );
}
