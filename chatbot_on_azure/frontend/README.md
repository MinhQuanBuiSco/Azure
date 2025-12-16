# Chatbot Frontend

Beautiful, modern React frontend for the Azure AI Chatbot application.

## Features

- ✨ Modern glassmorphism UI design
- 🎨 Gradient backgrounds with smooth animations
- 💬 Real-time chat interface
- 📱 Fully responsive design
- ⚡ Built with Vite for fast development
- 🎯 Tailwind CSS for styling
- 🚀 Production-ready Docker setup

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **Nginx** - Production server

## Development

### Prerequisites

- Node.js 20+
- npm or yarn

### Setup

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Update `.env` with your backend API URL:
```env
VITE_API_URL=http://localhost:8000
```

4. Start development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint

## Production Build

### Docker

Build the Docker image:
```bash
docker build -t chatbot-frontend:latest .
```

Run the container:
```bash
docker run -p 80:80 chatbot-frontend:latest
```

### Kubernetes Deployment

The frontend is designed to work with the included Kubernetes manifests in the `k8s/` directory.

Update the image in `k8s/frontend-deployment.yaml` and deploy:
```bash
kubectl apply -f k8s/frontend-deployment.yaml
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` |

## Design Features

### 2025 Modern UI Trends

- **Glassmorphism**: Frosted glass effect with backdrop blur
- **Animated Gradients**: Dynamic color transitions
- **Floating Elements**: Subtle 3D depth with animations
- **Smooth Transitions**: Polished micro-interactions
- **Clean Typography**: Modern, readable font hierarchy
- **Responsive Layout**: Mobile-first design approach

### Color Palette

- Primary: Purple to Pink gradient (`from-purple-500 to-pink-500`)
- Secondary: Blue to Cyan gradient (`from-blue-500 to-cyan-500`)
- Background: Multi-color animated gradient
- Accent: White with transparency for glassmorphism

## Architecture

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatMessage.jsx      # Message bubble component
│   │   └── TypingIndicator.jsx  # Loading indicator
│   ├── services/
│   │   └── api.js                # API client
│   ├── App.jsx                   # Main application
│   ├── main.jsx                  # Entry point
│   └── index.css                 # Global styles
├── public/                       # Static assets
├── Dockerfile                    # Production build
├── nginx.conf                    # Nginx configuration
└── package.json                  # Dependencies
```

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Performance

- Lazy loading for optimal performance
- Optimized bundle size
- Gzip compression enabled
- Static asset caching (1 year)
- Health check endpoint at `/health`

## License

MIT
