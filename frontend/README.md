# Atlas Data Pipeline Dashboard

Modern React dashboard for the Atlas Data Pipeline Platform with real-time quality metrics, PII detection, and connector management.

## Features

- **CSV Upload**: Drag-and-drop CSV upload with real-time processing
- **Quality Metrics**: 6-dimension data quality visualization (completeness, uniqueness, validity, consistency, accuracy, timeliness)
- **PII Detection**: Real-time PII detection with confidence scores and compliance reporting
- **Connectors**: Manage database and API connectors with scheduled syncs
- **Real-time Updates**: Auto-refreshing dashboard with React Query
- **Responsive Design**: Mobile-first design with Tailwind CSS
- **Professional UI**: Modern glassmorphism design with smooth animations

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **UI Library**: Tailwind CSS
- **State Management**: TanStack Query (React Query)
- **Routing**: React Router v6
- **File Upload**: react-dropzone
- **Forms**: React Hook Form + Zod
- **Charts**: Recharts
- **Icons**: Lucide React

## Quick Start

### Prerequisites

- Node.js 18+ installed
- Atlas API running at `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Open browser at http://localhost:5173
```

### Build for Production

```bash
# Build the application
npm run build

# Preview production build
npm run preview
```

## Environment Variables

Create a `.env` file in the root directory:

```env
VITE_API_URL=http://localhost:8000
```

## Project Structure

```
atlas-dashboard/
├── src/
│   ├── api/              # API client and endpoints
│   ├── components/       # React components
│   │   ├── Layout/       # Sidebar, Header, Layout
│   │   ├── Upload/       # CSV upload components
│   │   ├── Quality/      # Quality metrics components
│   │   ├── PII/          # PII detection components
│   │   └── Connectors/   # Connector management
│   ├── pages/            # Page components
│   ├── types/            # TypeScript type definitions
│   ├── hooks/            # Custom React hooks
│   ├── utils/            # Utility functions
│   ├── App.tsx           # Main app component
│   ├── main.tsx          # Entry point
│   └── index.css         # Global styles
├── public/               # Static assets
├── index.html            # HTML template
├── vite.config.ts        # Vite configuration
├── tailwind.config.js    # Tailwind configuration
└── tsconfig.json         # TypeScript configuration
```

## Available Pages

- **Dashboard** (`/`) - Overview with stats and recent runs
- **Upload CSV** (`/upload`) - Upload and process CSV files
- **Connectors** (`/connectors`) - Manage data connectors
- **Quality Reports** (`/reports`) - View all quality reports
- **PII Analysis** (`/pii`) - PII detection dashboard

## API Integration

The dashboard connects to the Atlas API at `http://localhost:8000`:

- `POST /pipeline/run` - Upload CSV file
- `GET /pipeline/status/{id}` - Get pipeline status
- `GET /quality/metrics/{id}` - Get quality metrics
- `GET /quality/pii-report/{id}` - Get PII report
- `GET /connectors/` - List connectors
- `POST /connectors/` - Create connector
- `POST /connectors/{id}/sync` - Trigger sync

## Development

### Running the Backend

Make sure the Atlas API is running:

```bash
cd /Users/sven/Desktop/MCP/.worktrees/atlas-api
python3 simple_main.py
```

### Hot Reload

The dashboard supports hot module replacement (HMR) for instant updates during development.

### Type Checking

```bash
npm run build  # TypeScript compilation is part of the build
```

## Performance

- Initial load: <2s
- Navigation: <500ms
- File upload: Real-time progress
- Auto-refresh: Every 30 seconds

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

ISC