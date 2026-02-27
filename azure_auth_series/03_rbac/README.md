# Blog 3: Role-Based Access Control (RBAC) with Azure AD App Roles

Add Admin, Editor, and Reader roles to your app using Azure AD App Roles. The backend enforces permissions, and the frontend adapts its UI per role.

## What You'll Build

- Three App Roles (Admin/Editor/Reader) defined in Azure AD
- Backend authorization that enforces role-based permissions
- Frontend UI that adapts based on the signed-in user's role
- Two test users to demo each role side-by-side

## Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.10+
- **Azure CLI** (`az`) — [install](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
- **Azure subscription** (free tier works)

## Quick Start

### 1. Setup (Azure CLI)

The setup script creates two app registrations, defines 3 App Roles, creates test users, and assigns roles.

```bash
az login
./setup.sh
```

This outputs a table with test account credentials.

### 2. Run the Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3. Run the Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Test Each Role

Sign in as each user to see different permissions:

| Role | What You See |
|---|---|
| **Admin** (your account) | All tasks from all users, full CRUD, delete button visible |
| **Editor** (testuser-editor) | Own tasks only, can create/edit, no delete |
| **Reader** (testuser-reader) | Own tasks only, read-only, no add/edit/delete |

### Cleanup

```bash
./cleanup.sh
```

## Architecture

```
Browser (Next.js + MSAL)
   │
   │  Bearer token (includes "roles" claim)
   ▼
FastAPI Backend
   ├── GET  /api/me            → any authenticated user
   ├── GET  /api/tasks         → Reader+ (Admin sees all)
   ├── POST /api/tasks         → Editor+
   ├── PATCH /api/tasks/:id    → Editor+ (own) / Admin (any)
   └── DELETE /api/tasks/:id   → Admin only
         │
         │  require_role("Admin", "Editor", ...)
         ▼
   Azure AD App Roles (in JWT token)
```

### Key Patterns

| Pattern | Implementation |
|---|---|
| Role definition | `appRoles` array in the API app registration manifest |
| Role assignment | Service principal → appRoleAssignments via Graph API |
| Backend enforcement | `require_role()` dependency checks `roles` claim in JWT |
| Frontend adaptation | Read `profile.roles`, conditionally render UI elements |
| Admin visibility | Admin sees all users' tasks; others see only their own |

## Tech Stack

- **Next.js 14** (App Router) + **MSAL React**
- **FastAPI** + **python-jose** (JWT + role validation)
- **Azure AD App Roles** (no database needed for authorization)
- **Tailwind CSS** + **shadcn/ui**
