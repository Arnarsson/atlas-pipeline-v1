# Quick Start Guide: Week 5-6 Features

## What's New? 🎉

Four new powerful features added to Atlas Dashboard:

### 1. 🔍 Data Catalog (`/catalog`)
**Browse and discover all your datasets**

- Search datasets by name/description
- Filter by tags (PII, GDPR, Finance, etc.)
- View detailed schema information
- Track quality score history
- Download schema as JSON

**Key Components:**
- Search bar with real-time filtering
- Tag filter buttons
- Dataset cards grid (responsive)
- Details modal with schema table

### 2. 📦 Feature Store (`/features`)
**Manage ML features with versioning**

- Register new feature groups
- Track feature versions
- Export in multiple formats (Parquet, CSV, JSON)
- View feature importance scores
- Monitor null/unique percentages

**Key Components:**
- Feature groups grid
- Upload modal for registration
- Version history viewer
- Export format selector
- Feature statistics table

### 3. 🛡️ GDPR Compliance (`/gdpr`)
**Handle data subject requests**

- Submit data export requests (Right to Access)
- Submit deletion requests (Right to be Forgotten)
- Track request status in real-time
- View compliance statistics
- Download exported data

**Key Components:**
- Compliance dashboard (4 stat cards)
- Request submission form
- Requests table with live updates
- Results modal with download

### 4. 🌳 Data Lineage (`/lineage`)
**Visualize data transformations**

- Interactive tree visualization
- Track data flow across layers (Explore → Chart → Navigate)
- Expand/collapse nodes
- View transformation operations
- Configurable depth (1-5 levels)

**Key Components:**
- Dataset selector
- Depth configuration
- Tree structure with connecting lines
- Layer legend (color-coded)

## Quick Access

### From Dashboard
New stat cards added:
- Feature Groups count
- Pending GDPR Requests
- Catalog Datasets
- Average Lineage Depth

### From Sidebar
Four new navigation items:
- Data Catalog (Search icon)
- Feature Store (Box icon)
- GDPR Compliance (Shield icon)
- Data Lineage (GitBranch icon)

## Running the Dashboard

```bash
# Navigate to dashboard
cd /Users/sven/Desktop/MCP/.worktrees/atlas-dashboard

# Install dependencies (if not already done)
npm install

# Start development server
npm run dev

# Dashboard will open at http://localhost:5173
```

## Testing the New Features

### 1. Test Data Catalog
```bash
# Navigate to http://localhost:5173/catalog
# Try searching for datasets
# Click on a dataset card to see details
# Filter by different tags
```

### 2. Test Feature Store
```bash
# Navigate to http://localhost:5173/features
# Click "Register Feature Group"
# Upload a CSV file
# View the feature groups
# Try exporting in different formats
```

### 3. Test GDPR Compliance
```bash
# Navigate to http://localhost:5173/gdpr
# Fill out the request form
# Submit an export request
# Submit a deletion request
# Check the requests table
```

### 4. Test Data Lineage
```bash
# Navigate to http://localhost:5173/lineage
# Select a dataset from dropdown
# Adjust the depth slider
# Expand/collapse nodes in the tree
```

## API Endpoints Expected

The frontend expects these backend endpoints:

### Data Catalog
- `GET /catalog/datasets?query=&tags=` - Search datasets
- `GET /catalog/dataset/{id}` - Get dataset details
- `GET /catalog/dataset/{id}/quality` - Get quality history

### Feature Store
- `GET /features/groups` - List feature groups
- `POST /features/groups` - Register new group (multipart/form-data)
- `GET /features/{name}/versions` - Get version history
- `POST /features/{name}/export` - Export features

### GDPR
- `POST /gdpr/export` - Request data export
- `POST /gdpr/delete` - Request data deletion
- `GET /gdpr/requests?subject_id=` - List requests

### Lineage
- `GET /lineage/dataset/{name}?depth=` - Get dataset lineage
- `GET /lineage/run/{runId}` - Get run lineage

## Design System

### Color Palette
- **Explore Layer**: Blue (`bg-blue-100 text-blue-800`)
- **Chart Layer**: Green (`bg-green-100 text-green-800`)
- **Navigate Layer**: Purple (`bg-purple-100 text-purple-800`)
- **Primary Actions**: Primary-600 (`bg-primary-600`)
- **Success**: Green-500
- **Warning**: Orange-500
- **Error**: Red-500

### Icons
- Data Catalog: Search
- Feature Store: Box
- GDPR: Shield
- Lineage: GitBranch
- Database: Database
- Download: Download
- Upload: Upload

### Responsive Breakpoints
- Mobile: `< 768px` (1 column)
- Tablet: `768px - 1024px` (2 columns)
- Desktop: `> 1024px` (3-4 columns)

## Troubleshooting

### Build Errors
```bash
# Clear cache and rebuild
rm -rf node_modules dist
npm install
npm run build
```

### TypeScript Errors
All type definitions are in `src/types/index.ts`. If you get type errors:
1. Check that types match API responses
2. Ensure imports are correct
3. Run `npm run build` to see all errors

### API Connection Issues
1. Verify backend is running on `http://localhost:8000`
2. Check CORS is enabled on backend
3. Verify API endpoints match expected paths
4. Check browser console for network errors

### Empty States
If you see "No data" messages:
1. This is expected if backend hasn't populated data
2. Pages will show helpful empty states
3. No errors should occur
4. UI remains functional

## File Structure

```
src/
├── api/
│   └── client.ts              # Added Week 5-6 endpoints
├── pages/
│   ├── DataCatalog.tsx        # NEW: Data Catalog page
│   ├── FeatureStore.tsx       # NEW: Feature Store page
│   ├── GDPR.tsx               # NEW: GDPR Compliance page
│   └── Lineage.tsx            # NEW: Data Lineage page
├── types/
│   └── index.ts               # Added Week 5-6 types
├── components/
│   └── Layout/
│       └── Sidebar.tsx        # Added 4 new nav items
└── App.tsx                    # Added 4 new routes
```

## Next Steps

1. **Backend Integration**: Connect to real API endpoints
2. **Data Population**: Add test datasets via catalog/features
3. **E2E Testing**: Test full workflows
4. **User Acceptance**: Get feedback on UI/UX
5. **Performance**: Monitor and optimize if needed

## Success Metrics

✅ All 4 pages render without errors
✅ Navigation works between pages
✅ Forms accept input and validate
✅ Modals open and close
✅ Responsive design works on mobile
✅ Loading states display correctly
✅ Empty states are helpful
✅ Build succeeds without warnings

---

**You're all set!** 🚀 Start the dashboard and explore the new features.
