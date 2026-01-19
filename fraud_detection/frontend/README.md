# Fraud Detection Frontend

Modern, responsive frontend built with React, TypeScript, Tailwind CSS, and shadcn/ui components. Designed with 2025 UI/UX trends in mind.

## Features

- **Real-time Dashboard** - Live transaction monitoring with fraud metrics
- **Transaction Management** - Browse and analyze transactions with risk scores
- **Alert Queue** - Manage and investigate fraud alerts
- **Analytics** - Visualize fraud trends and rule performance
- **Dark Mode** - Built-in theme support
- **Responsive Design** - Mobile-first, works on all screen sizes

## Tech Stack

- **Framework**: React 18 + Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4-ready design system
- **UI Components**: shadcn/ui-inspired components
- **Routing**: React Router v6
- **State Management**: TanStack Query (React Query)
- **Charts**: Recharts
- **Animations**: Framer Motion
- **Icons**: Lucide React

## Getting Started

### Installation

\`\`\`bash
npm install
cp .env.example .env
\`\`\`

### Development

\`\`\`bash
npm run dev          # Start dev server (http://localhost:5173)
npm run build        # Build for production
npm run preview      # Preview production build
\`\`\`

## Project Structure

\`\`\`
frontend/
├── src/
│   ├── components/ui/       # shadcn/ui-style components
│   ├── pages/               # Page components
│   ├── lib/                 # API client & utilities
│   └── App.tsx              # Main app with routing
├── tailwind.config.js
└── package.json
\`\`\`

## License

MIT License
