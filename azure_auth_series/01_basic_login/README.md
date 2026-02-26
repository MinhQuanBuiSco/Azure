# Blog 1: Basic Login with Microsoft Entra ID

Add enterprise-grade authentication to a Next.js app using MSAL React and Microsoft Graph API.

## What You'll Build

- A beautiful landing page with Microsoft sign-in
- A protected dashboard that displays your profile from the Graph API
- Popup-based authentication flow with automatic token management

## Prerequisites

- **Node.js** 18+ and npm
- **Azure CLI** (`az`) — [install](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
- **Azure subscription** (free tier works)
- **Microsoft Entra ID** (Azure AD) tenant

## Quick Start

### 1. Register the App (Azure CLI)

The setup script creates the app registration, configures the SPA redirect URI, adds the `User.Read` Graph API permission, and writes `frontend/.env.local` automatically.

```bash
az login
./setup.sh              # uses default name "Blog1-BasicLogin"
./setup.sh MyAppName    # or pass a custom name
```

This outputs your `client_id` and `tenant_id` and writes them to `frontend/.env.local`.

### 2. Run the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Manual Setup (Alternative)

If you prefer to register the app manually instead of using the script:

1. Go to [Azure Portal](https://portal.azure.com) → **Microsoft Entra ID** → **App registrations** → **New registration**
2. Set **Name**, **Redirect URI** → SPA → `http://localhost:3000`, then click **Register**
3. Copy the **Application (client) ID** and **Directory (tenant) ID** from the Overview page
4. Verify `User.Read` is listed under **API permissions**
5. Create `frontend/.env.local` from the example and paste your IDs:
   ```bash
   cp frontend/.env.local.example frontend/.env.local
   ```

## Architecture

```
src/
├── app/
│   ├── layout.tsx          # Root layout with MsalProvider + Navbar + Footer
│   ├── page.tsx            # Landing page (Hero + Features)
│   └── dashboard/
│       └── page.tsx        # Protected dashboard (profile + token info)
├── components/
│   ├── auth/
│   │   ├── msal-provider.tsx   # MSAL singleton initialization + MsalProvider
│   │   ├── login-button.tsx    # Sign in with popup
│   │   ├── logout-button.tsx   # Sign out with popup
│   │   └── user-profile.tsx    # Avatar + dropdown menu
│   ├── layout/
│   │   ├── navbar.tsx          # Responsive nav with auth state
│   │   └── footer.tsx          # Site footer
│   └── landing/
│       ├── hero.tsx            # Hero section with CTA
│       └── features.tsx        # Feature cards
├── config/
│   └── auth-config.ts     # MSAL configuration + scopes
├── hooks/
│   └── use-graph.ts       # Token acquisition + Graph API calls
├── lib/
│   └── graph.ts           # Graph API helper functions
└── types/
    └── index.ts           # TypeScript interfaces
```

### Key Patterns

| Pattern | Implementation |
|---|---|
| MSAL initialization | Singleton `PublicClientApplication` created at module scope in `msal-provider.tsx` |
| Auth flow | Popup-based login/logout (no redirect routing conflicts) |
| Token acquisition | `acquireTokenSilent` → fallback to `acquireTokenPopup` |
| State management | MSAL React hooks (`useMsal`, `useIsAuthenticated`) |
| API calls | Fetch with Bearer token to Microsoft Graph |

## Tech Stack

- **Next.js 14** (App Router, React 18)
- **MSAL React v2** + **MSAL Browser v3**
- **Tailwind CSS** + **shadcn/ui**
- **Microsoft Graph API**
- **TypeScript**
