import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import Connectors from './pages/Connectors';
import QualityReports from './pages/QualityReports';
import PIIAnalysis from './pages/PIIAnalysis';
import DataCatalog from './pages/DataCatalog';
import FeatureStore from './pages/FeatureStore';
import GDPR from './pages/GDPR';
import Lineage from './pages/Lineage';
import AtlasIntelligence from './pages/AtlasIntelligence';
import Decisions from './pages/Decisions';
import Inbox from './pages/Inbox';
// New pages for Airbyte-style UI
import SourceCatalog from './pages/SourceCatalog';
import Connections from './pages/Connections';
import SyncJobs from './pages/SyncJobs';
import ConnectorHealth from './pages/ConnectorHealth';
import Credentials from './pages/Credentials';
import Schedules from './pages/Schedules';
import RBAC from './pages/RBAC';
import KPIDashboard from './pages/KPIDashboard';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: 'hsl(var(--card))',
              color: 'hsl(var(--foreground))',
              fontWeight: '500',
              borderRadius: '8px',
              padding: '12px 16px',
              border: '1px solid hsl(var(--border))',
            },
            success: {
              iconTheme: {
                primary: '#10b981',
                secondary: '#fff',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
        <Routes>
          <Route path="/" element={<Layout />}>
            {/* Home */}
            <Route index element={<Dashboard />} />

            {/* Sources */}
            <Route path="connections" element={<Connections />} />
            <Route path="sources" element={<SourceCatalog />} />
            <Route path="credentials" element={<Credentials />} />

            {/* Syncs */}
            <Route path="sync-jobs" element={<SyncJobs />} />
            <Route path="schedules" element={<Schedules />} />
            <Route path="health" element={<ConnectorHealth />} />

            {/* Data */}
            <Route path="catalog" element={<DataCatalog />} />
            <Route path="reports" element={<QualityReports />} />
            <Route path="pii" element={<PIIAnalysis />} />
            <Route path="lineage" element={<Lineage />} />
            <Route path="features" element={<FeatureStore />} />

            {/* Governance */}
            <Route path="gdpr" element={<GDPR />} />
            <Route path="decisions" element={<Decisions />} />
            <Route path="rbac" element={<RBAC />} />

            {/* Legacy routes (keep for backwards compatibility) */}
            <Route path="upload" element={<Upload />} />
            <Route path="connectors" element={<Connectors />} />
            <Route path="atlas-intelligence" element={<AtlasIntelligence />} />
            <Route path="inbox" element={<Inbox />} />
            <Route path="kpi" element={<KPIDashboard />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
