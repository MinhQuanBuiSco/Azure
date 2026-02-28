import { Shield } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t py-8 mt-auto">
      <div className="container flex flex-col items-center gap-4 px-4 mx-auto max-w-6xl md:flex-row md:justify-between">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Shield className="h-4 w-4" />
          <span>Azure Auth Series &mdash; Blog 7: API Gateway</span>
        </div>
        <p className="text-xs text-muted-foreground">
          Built with Next.js, MSAL React &amp; FastAPI
        </p>
      </div>
    </footer>
  );
}
