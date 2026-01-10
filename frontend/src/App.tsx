import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
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

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
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
          </Route>
        </Routes>
      </Router>
      <Toaster position="top-right" />
    </QueryClientProvider>
  );
}

export default App;
