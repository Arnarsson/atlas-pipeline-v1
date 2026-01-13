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
              background: '#1e3a8a',
              color: '#fff',
              fontWeight: '600',
              borderRadius: '12px',
              padding: '16px',
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
            <Route index element={<Dashboard />} />
            <Route path="upload" element={<Upload />} />
            <Route path="connectors" element={<Connectors />} />
            <Route path="reports" element={<QualityReports />} />
            <Route path="pii" element={<PIIAnalysis />} />
            <Route path="catalog" element={<DataCatalog />} />
            <Route path="features" element={<FeatureStore />} />
            <Route path="gdpr" element={<GDPR />} />
            <Route path="lineage" element={<Lineage />} />
            <Route path="atlas-intelligence" element={<AtlasIntelligence />} />
            <Route path="decisions" element={<Decisions />} />
            <Route path="inbox" element={<Inbox />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
