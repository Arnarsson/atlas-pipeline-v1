# Atlas Dashboard - Quick Start Guide

Get the Atlas Data Pipeline Dashboard running in **under 2 minutes**.

## Prerequisites Check

```bash
# Check Node.js version (need 18+)
node --version

# Check if Atlas API is running
curl http://localhost:8000/docs
```

## Installation (30 seconds)

```bash
# Navigate to dashboard directory
cd /Users/sven/Desktop/MCP/.worktrees/atlas-dashboard

# Install dependencies (already done if you see node_modules/)
npm install
```

## Start the Dashboard (5 seconds)

```bash
# Start the development server
npm run dev
```

You should see:
```
VITE v7.3.1 ready in 891 ms

➜  Local:   http://localhost:5173/
```

## Open in Browser

Open **http://localhost:5173/** in your browser.

You should see:
- **Atlas Pipeline** dashboard with a sidebar
- **Dashboard** page with stats cards
- Navigation to Upload, Connectors, Reports, and PII Analysis

## Test the Upload Feature

1. Click **"Upload CSV"** in the sidebar
2. Drag and drop a CSV file (or click to browse)
3. Enter a dataset name
4. Click **"Upload & Process"**
5. Watch real-time quality metrics and PII detection results appear

## What You Get

### Dashboard Page (`/`)
- Total pipeline runs
- Average quality score
- PII detections count
- Active connectors
- Recent runs table
- Quick action cards

### Upload CSV Page (`/upload`)
- Drag-and-drop file upload
- Real-time processing
- Quality metrics (6 dimensions)
- PII detection results
- Download report button

### Components Built
- ✅ Sidebar navigation
- ✅ Header with search
- ✅ Quality dimension cards
- ✅ PII detection table
- ✅ CSV dropzone
- ✅ Responsive layouts

### API Integration
All endpoints connected to `http://localhost:8000`:
- ✅ `/pipeline/run` - CSV upload
- ✅ `/quality/metrics/{id}` - Quality data
- ✅ `/quality/pii-report/{id}` - PII results
- ✅ `/dashboard/stats` - Dashboard stats

## Current Status

**Working Features:**
- Dashboard with stats and recent runs
- CSV upload with drag-and-drop
- Quality metrics visualization (6 dimensions)
- PII detection table
- Responsive design (mobile-friendly)
- Real-time updates (React Query)

**Coming Soon:**
- Connectors page (full CRUD)
- Quality reports list page
- PII analysis dashboard
- Advanced filtering and search
- Report download (PDF/JSON)

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 5173
lsof -ti:5173 | xargs kill -9

# Or use a different port
npm run dev -- --port 3000
```

### API Connection Issues
```bash
# Verify API is running
curl http://localhost:8000/docs

# Start API if needed
cd /Users/sven/Desktop/MCP/.worktrees/atlas-api
python3 simple_main.py
```

### Build Errors
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

## Next Steps

1. **Test the upload**: Upload a sample CSV file
2. **Check quality metrics**: View the 6-dimension dashboard
3. **Review PII detections**: See what sensitive data was found
4. **Explore the code**: Check `/src/components` and `/src/pages`
5. **Customize**: Modify colors in `tailwind.config.js`

## Development Tips

- **Hot reload**: Changes automatically refresh in browser
- **TypeScript**: Full type safety throughout
- **React Query**: Automatic caching and refetching
- **Tailwind**: Utility-first CSS for rapid styling
- **Lucide Icons**: Beautiful icon library

## File Locations

- **Components**: `/src/components/`
- **Pages**: `/src/pages/`
- **API Client**: `/src/api/client.ts`
- **Types**: `/src/types/index.ts`
- **Config**: `vite.config.ts`, `tailwind.config.js`

## Support

- Check `README.md` for full documentation
- View API docs at `http://localhost:8000/docs`
- Inspect browser console for errors
- Check network tab for API calls

---

**Enjoy your modern data pipeline dashboard!** 🚀
