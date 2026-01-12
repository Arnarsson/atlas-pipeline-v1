# Atlas Dashboard Frontend - CLAUDE.md

**Last Updated**: January 12, 2026
**Status**: UI Redesign Complete - Linear/Vercel Aesthetic
**Tech Stack**: React 18 + TypeScript + Vite + Tailwind CSS v4 + shadcn/ui

---

## Project Overview

Modern React dashboard for the Atlas Data Pipeline Platform. Features 9 pages for data pipeline management, quality monitoring, GDPR compliance, and feature store management.

### Quick Start

```bash
cd /Users/sven/Desktop/MCP/.worktrees/atlas-dashboard/frontend
npm install
npm run dev
# Dashboard: http://localhost:5173
```

**Backend Required**: Start the API server first:
```bash
cd /Users/sven/Desktop/MCP/.worktrees/atlas-api
python3 simple_main.py
# API: http://localhost:8000
```

---

## Current Design System (January 2026)

### Linear/Vercel Aesthetic
- **Minimal, neutral color palette** - No colorful gradients
- **CSS Variables** for theming with HSL values
- **Dark mode support** via `.dark` class on `<html>`
- **shadcn/ui components** (Card, Button) with Radix primitives

### Color Tokens (index.css)
```css
:root {
  --background: 0 0% 100%;
  --foreground: 0 0% 3.9%;
  --card: 0 0% 100%;
  --muted: 0 0% 96.1%;
  --muted-foreground: 0 0% 45.1%;
  --border: 0 0% 89.8%;
  --input: 0 0% 89.8%;
  --ring: 0 0% 3.9%;
  --secondary: 0 0% 96.1%;
}

.dark {
  --background: 0 0% 3.9%;
  --foreground: 0 0% 98%;
  /* ... dark mode values */
}
```

### Usage Pattern (Tailwind v4)
```tsx
// DO: Use CSS variable syntax
className="text-[hsl(var(--foreground))]"
className="bg-[hsl(var(--secondary))]"
className="border-[hsl(var(--border))]"

// DON'T: Use semantic color classes (breaks in Tailwind v4)
className="text-foreground"  // Error!
className="border-border"    // Error!
```

### Semantic Colors (Reserved)
- **Green** (`bg-green-500/10 text-green-600`): Success, completed, validated
- **Red** (`bg-red-500/10 text-red-600`): Error, failed, delete actions
- **Neutral**: Everything else uses CSS variables

---

## File Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts          # API client with React Query integration
│   ├── components/
│   │   ├── ui/
│   │   │   ├── button.tsx     # shadcn Button component
│   │   │   └── card.tsx       # shadcn Card component
│   │   ├── Layout/
│   │   │   ├── Layout.tsx     # Main layout with sidebar
│   │   │   ├── Header.tsx     # Top header with dark mode toggle
│   │   │   └── Sidebar.tsx    # Navigation sidebar
│   │   ├── Connectors/        # Connector wizard components
│   │   ├── Quality/           # Quality dashboard components
│   │   ├── PII/               # PII analysis components
│   │   ├── Upload/            # CSV dropzone
│   │   ├── Lineage/           # Lineage graph visualization
│   │   └── ErrorBoundary.tsx  # Error boundary wrapper
│   ├── pages/
│   │   ├── Dashboard.tsx      # Main dashboard with stats
│   │   ├── Upload.tsx         # CSV upload with quality/PII viz
│   │   ├── Connectors.tsx     # Connector management
│   │   ├── QualityReports.tsx # Quality reports list
│   │   ├── PIIAnalysis.tsx    # PII detection dashboard
│   │   ├── DataCatalog.tsx    # Dataset browser
│   │   ├── FeatureStore.tsx   # ML feature management
│   │   ├── GDPR.tsx           # GDPR compliance workflows
│   │   └── Lineage.tsx        # Data lineage visualization
│   ├── lib/
│   │   └── utils.ts           # cn() utility for class merging
│   ├── types/
│   │   └── index.ts           # TypeScript interfaces
│   ├── index.css              # Global styles + CSS variables
│   ├── App.tsx                # Router setup
│   └── main.tsx               # Entry point
├── tests/
│   └── e2e/                   # Playwright E2E tests (12 spec files)
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

---

## Key Components

### shadcn/ui Components

**Button** (`src/components/ui/button.tsx`):
```tsx
import { Button } from '@/components/ui/button';

<Button>Default</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button size="sm">Small</Button>
```

**Card** (`src/components/ui/card.tsx`):
```tsx
import { Card, CardContent } from '@/components/ui/card';

<Card>
  <CardContent className="p-6">
    Content here
  </CardContent>
</Card>
```

### Layout Components

**Dark Mode Toggle** (in Header.tsx):
```tsx
const [isDark, setIsDark] = useState(false);

useEffect(() => {
  document.documentElement.classList.toggle('dark', isDark);
}, [isDark]);
```

---

## API Integration

### React Query Setup
```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { searchDatasets, uploadCSV } from '@/api/client';

// Fetching data
const { data, isLoading } = useQuery({
  queryKey: ['datasets', searchQuery],
  queryFn: () => searchDatasets(searchQuery),
});

// Mutations
const mutation = useMutation({
  mutationFn: uploadCSV,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['datasets'] });
    toast.success('Upload complete');
  },
});
```

### API Endpoints Used
- `GET /dashboard/stats` - Dashboard overview
- `POST /pipeline/run` - Upload CSV
- `GET /quality/metrics/{run_id}` - Quality scores
- `GET /quality/pii-report/{run_id}` - PII detections
- `GET /connectors/` - List connectors
- `GET /catalog/datasets` - Search datasets
- `GET /features/groups` - Feature groups
- `GET /gdpr/requests` - GDPR requests
- `GET /lineage/dataset/{name}` - Lineage graph

---

## Testing

### Playwright E2E Tests
```bash
# Run all tests
npm run test:e2e

# Interactive UI mode
npm run test:e2e:ui

# View report
npm run test:e2e:report
```

### Test Files
- `01-navigation.spec.ts` - Page navigation
- `02-csv-upload.spec.ts` - File upload flow
- `03-connectors.spec.ts` - Connector wizard
- `04-quality-reports.spec.ts` - Quality filtering
- `05-gdpr.spec.ts` - GDPR workflows
- `06-catalog.spec.ts` - Dataset search
- `07-features.spec.ts` - Feature store
- `08-user-journey.spec.ts` - Full user flows
- `09-performance.spec.ts` - Load time tests
- `10-visual.spec.ts` - Visual regression
- `11-api-contracts.spec.ts` - API structure validation
- `12-error-handling.spec.ts` - Error scenarios

---

## Development Guidelines

### Adding New Pages
1. Create page component in `src/pages/`
2. Add route in `src/App.tsx`
3. Add navigation link in `src/components/Layout/Sidebar.tsx`
4. Use existing patterns for data fetching (React Query)
5. Use CSS variable syntax for all colors

### Style Patterns

**Form Inputs**:
```tsx
<input
  className="w-full px-3 py-2 border border-[hsl(var(--input))] rounded-md bg-[hsl(var(--background))] text-[hsl(var(--foreground))] placeholder:text-[hsl(var(--muted-foreground))] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
/>
```

**Modals**:
```tsx
<div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
  <div className="bg-[hsl(var(--card))] rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto border border-[hsl(var(--border))]">
```

**Status Badges**:
```tsx
// Success
<span className="px-2 py-1 text-xs font-medium rounded bg-green-500/10 text-green-600">
  Completed
</span>

// Error
<span className="px-2 py-1 text-xs font-medium rounded bg-red-500/10 text-red-600">
  Failed
</span>

// Neutral
<span className="px-2 py-1 text-xs font-medium rounded bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))]">
  Pending
</span>
```

---

## Known Issues & Notes

### Tailwind CSS v4 Compatibility
- Use `@import "tailwindcss"` in index.css (not `@tailwind` directives)
- Semantic color classes (`text-foreground`, `border-border`) don't work
- Must use arbitrary value syntax: `text-[hsl(var(--foreground))]`

### Browser Caching
After CSS changes, do a hard refresh:
- **Mac**: Cmd + Shift + R
- **Windows/Linux**: Ctrl + Shift + R

### Port Numbers
- Frontend: 5173 (default Vite port)
- Backend API: 8000

---

## Recent Changes (January 2026)

### UI Redesign to Linear/Vercel Aesthetic
- Removed all colorful gradients (purple, blue, orange)
- Implemented CSS variable theming
- Added dark mode toggle in header
- Updated all 9 pages with new design system
- Created shadcn/ui Button and Card components
