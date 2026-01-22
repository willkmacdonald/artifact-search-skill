# Frontend Architecture Specification

## Overview

The artifact-search-skill frontend is a Next.js 14 application providing a chat-style interface for searching MedTech risk management artifacts. Users ask natural language questions and receive AI-summarized results from Azure DevOps, Figma, Notion, and Ice Panel.

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Framework | Next.js | 14.1.0 | React framework with App Router |
| UI Library | React | 18 | Component library |
| Styling | Tailwind CSS | 3.3.0 | Utility-first CSS |
| Icons | Lucide React | 0.312.0 | Icon components |
| Language | TypeScript | 5 | Type safety |

## Project Structure

```
frontend/
├── package.json          # Dependencies and scripts
├── next.config.js        # Next.js configuration (API proxy)
├── tailwind.config.ts    # Tailwind theme customization
├── tsconfig.json         # TypeScript configuration
├── postcss.config.mjs    # PostCSS for Tailwind
└── src/
    └── app/
        ├── layout.tsx    # Root layout with metadata
        ├── page.tsx      # Main chat interface (single page)
        └── globals.css   # Global styles + Tailwind imports
```

## Architecture

### Single-Page Application

The frontend is a single-page chat interface (`src/app/page.tsx`) that:
1. Displays connection status to backend
2. Shows configured data sources
3. Provides chat input for queries
4. Renders AI responses with artifact cards

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         React Component                              │
│                          (page.tsx)                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │ Connection   │    │ Chat Input   │    │ Message List         │  │
│  │ Status       │    │              │    │ (user + assistant)   │  │
│  └──────────────┘    └──────────────┘    └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   fetch()       │
                    │   /api/*        │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Next.js Proxy  │
                    │ (next.config.js)│
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  FastAPI Backend│
                    │  localhost:8000 │
                    └─────────────────┘
```

## Component Structure

The main page component (`page.tsx`) contains:

### State Management

```typescript
const [messages, setMessages] = useState<ChatMessage[]>([]);
const [input, setInput] = useState("");
const [isLoading, setIsLoading] = useState(false);
const [connectionStatus, setConnectionStatus] = useState<"checking" | "connected" | "error">("checking");
const [configuredSources, setConfiguredSources] = useState<string[]>([]);
```

### Key Functions

| Function | Purpose |
|----------|---------|
| `checkHealth()` | Calls `/api/health` on mount to verify backend connection |
| `handleSubmit()` | Sends user message to `/api/chat`, updates message list |
| `handleSuggestionClick()` | Populates input with suggested query |

## TypeScript Interfaces

```typescript
interface Artifact {
  id: string;
  source: string;           // "azure_devops" | "figma" | "notion" | "icepanel"
  type: string;             // "risk" | "mitigation" | "design" | etc.
  title: string;
  content: string;
  url: string | null;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  artifacts?: Artifact[];
  sources?: string[];
  isLoading?: boolean;
}
```

## UI Components

### Header
- App branding (MedTech Risk Copilot)
- Connection status indicator (checking/connected/error)

### Source Bar
- Shows configured sources as colored badges
- Each source has unique icon and color scheme

### Chat Area
- Empty state with welcome message and suggested queries
- Message bubbles (user = blue, assistant = white)
- Artifact cards with source/type badges and external links

### Input Area
- Text input for queries
- Send button with loading state
- Disabled when backend offline

## Styling System

### Source Colors

```typescript
const sourceColors: Record<string, string> = {
  azure_devops: "bg-blue-100 text-blue-800 border-blue-200",
  figma: "bg-purple-100 text-purple-800 border-purple-200",
  notion: "bg-gray-100 text-gray-800 border-gray-200",
  icepanel: "bg-cyan-100 text-cyan-800 border-cyan-200",
};
```

### Artifact Type Colors

```typescript
const typeColors: Record<string, string> = {
  risk: "bg-red-100 text-red-800",
  mitigation: "bg-green-100 text-green-800",
  requirement: "bg-blue-100 text-blue-800",
  design: "bg-purple-100 text-purple-800",
  architecture: "bg-cyan-100 text-cyan-800",
  work_item: "bg-yellow-100 text-yellow-800",
  test_case: "bg-orange-100 text-orange-800",
  document: "bg-gray-100 text-gray-800",
};
```

### Custom Theme (tailwind.config.ts)

```typescript
colors: {
  primary: {
    50: "#eff6ff",
    // ... blue scale for brand color
    600: "#2563eb",  // Primary actions
    700: "#1d4ed8",  // Hover states
  },
}
```

## API Integration

### Proxy Configuration (next.config.js)

```javascript
async rewrites() {
  return [
    {
      source: "/api/:path*",
      destination: "http://localhost:8000/:path*",
    },
  ];
}
```

### API Calls

| Endpoint | Method | When Called |
|----------|--------|-------------|
| `/api/health` | GET | On component mount |
| `/api/chat` | POST | When user submits query |

### Error Handling

- Backend offline: Shows "Backend offline" status, disables input
- Request failures: Shows error message in chat, continues to allow input

## Suggested Queries

Pre-defined example queries to guide users:

```typescript
const suggestedQueries = [
  "What are the risks related to arrhythmia detection?",
  "Show me mitigations for patient data security",
  "Find the UI designs for alert configuration",
  "What is the system architecture for CardioWatch?",
  "Show requirements linked to RISK-001",
];
```

## Responsive Design

- Max width container (`max-w-4xl`) for readability
- Flexbox layout for header, chat, and input areas
- Full-height layout with scrollable chat area
- Mobile-friendly input and button sizing

## Icons (Lucide React)

| Icon | Usage |
|------|-------|
| `Shield` | App logo, welcome state |
| `Send` | Submit button |
| `Loader2` | Loading states (animated spin) |
| `ExternalLink` | Artifact URL links |
| `AlertCircle` | Error status |
| `CheckCircle2` | Connected status |
| `Database` | Azure DevOps source |
| `Palette` | Figma source |
| `FileText` | Notion source |
| `Network` | Ice Panel source |

## Build & Development

### Scripts

```json
{
  "dev": "next dev",           // Development server (port 3000)
  "build": "next build",       // Production build
  "start": "next start",       // Production server
  "lint": "next lint"          // ESLint
}
```

### Development Requirements

- Node.js (version compatible with Next.js 14)
- Backend running on `localhost:8000`

## Deployment Considerations

### Current State
- Development-only (localhost proxy)
- No environment variable configuration
- No static export

### For Production (Azure Static Web Apps)
1. Add `output: 'export'` to next.config.js
2. Use `NEXT_PUBLIC_API_URL` environment variable
3. Update API calls to use configurable base URL
4. Configure CORS on backend for SWA domain

## Future Enhancements

- Conversation history persistence
- Streaming responses
- Artifact detail modal/drawer
- Search filters (by source, type, date)
- Dark mode support
