# LLM Security Gateway - Frontend

Next.js dashboard for monitoring and testing the LLM Security Gateway.

## Features

- **Dashboard**: Overview metrics, charts, and recent requests
- **Audit Logs**: Searchable/filterable request history
- **Security Playground**: Test prompts with pre-built attack examples
- **Settings**: View configuration and system status

## Quick Start

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
npm start
```

## Pages

- `/` - Dashboard with metrics and charts
- `/audit` - Audit log viewer
- `/playground` - Security testing playground
- `/settings` - Configuration and status

## Configuration

Environment variables:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Components

```
src/
├── app/                    # Next.js App Router
│   ├── page.tsx           # Dashboard
│   ├── audit/page.tsx     # Audit logs
│   ├── playground/page.tsx # Security testing
│   └── settings/page.tsx  # Settings
├── components/
│   ├── ui/                # Shadcn components
│   ├── dashboard/         # Dashboard components
│   ├── playground/        # Playground components
│   └── shared/            # Shared components
└── lib/
    ├── api.ts             # API client
    ├── examples.ts        # Test prompt examples
    └── utils.ts           # Utilities
```

## Security Testing Playground

The playground includes pre-built examples for:
- Prompt injection attacks
- Jailbreak attempts (DAN, developer mode, etc.)
- PII exposure testing
- Secret/credential detection
- Benign prompts for comparison

## Tech Stack

- Next.js 14 with App Router
- TypeScript
- Tailwind CSS
- Shadcn/ui components
- Recharts for visualization

## Docker

```bash
docker build -t llm-gateway-frontend .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://localhost:8000 llm-gateway-frontend
```
