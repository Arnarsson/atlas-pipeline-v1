# Atlas Dashboard - Quick Start Guide

## 🚀 Running the Application

The dashboard is **LIVE** at: **http://localhost:5173**

```bash
cd /Users/sven/Desktop/MCP/.worktrees/atlas-dashboard
npm run dev
```

## 📱 Available Pages

### 1. Dashboard (Home)
**URL**: http://localhost:5173/

- Overview statistics
- Recent pipeline runs
- Quality score trends
- PII detection summary

### 2. Upload CSV
**URL**: http://localhost:5173/upload

- Drag-and-drop CSV upload
- Real-time processing status
- Quality metrics visualization
- PII detection results

### 3. Connectors
**URL**: http://localhost:5173/connectors

**Features**:
- View all data connectors
- Create new connector (5-step wizard)
- Edit existing connectors
- Delete connectors
- Trigger manual sync
- View sync history

**Supported Types**:
- 🐘 PostgreSQL
- 🐬 MySQL
- 🌐 REST API

**Try It**:
1. Click "New Connector"
2. Select PostgreSQL
3. Fill in connection details
4. Set up schedule (or leave as Manual)
5. Test connection
6. Review and create

### 4. Quality Reports
**URL**: http://localhost:5173/reports

**Features**:
- Browse all quality reports
- Search by dataset name
- Filter by date range
- Filter by quality score (0-100%)
- Filter by PII status
- View detailed breakdowns
- Download JSON reports

**Try It**:
1. Upload a CSV from Upload page
2. Navigate to Quality Reports
3. Click on a report to see details
4. Explore 6 quality dimensions
5. Review column-level metrics

### 5. PII Analysis
**URL**: http://localhost:5173/pii

**Features**:
- PII detection statistics
- Interactive pie chart (click to filter)
- Compliance status (GDPR)
- High-risk alerts
- PII inventory table
- Export to CSV

**Try It**:
1. View PII distribution chart
2. Click on a PII type to filter
3. Check compliance recommendations
4. Export inventory to CSV

## 🎯 Key Features

### Connector Wizard
**5-Step Process**:
1. **Type**: Select data source type
2. **Config**: Enter connection details
3. **Schedule**: Set up cron schedule (or manual)
4. **Test**: Verify connection works
5. **Review**: Confirm and create

### Cron Scheduler
**Presets Available**:
- Every hour
- Every day at midnight
- Every day at 9 AM
- Every Monday at 9 AM
- First day of month
- Manual (no schedule)
- Custom (define your own)

**Custom Cron Format**: `minute hour day month day-of-week`

Example: `0 9 * * 1-5` = Every weekday at 9:00 AM

### Quality Dimensions
1. **Completeness**: Are all values present?
2. **Uniqueness**: Are values unique when expected?
3. **Validity**: Do values match expected formats?
4. **Consistency**: Are values consistent across dataset?
5. **Accuracy**: Are values within expected ranges?
6. **Timeliness**: Is data fresh and up-to-date?

### PII Types Detected
- EMAIL_ADDRESS
- PERSON (names)
- PHONE_NUMBER
- CREDIT_CARD
- US_SSN
- DK_CPR (Danish CPR number)
- US_BANK_NUMBER
- IBAN_CODE
- IP_ADDRESS
- And more...

## ⚙️ Configuration

### Environment Variables
Create `.env` file:
```env
VITE_API_URL=http://localhost:8000
```

Default: `http://localhost:8000` (Atlas API backend)

### Backend Requirements
The dashboard expects the Atlas API to be running at `http://localhost:8000`

**Start Backend**:
```bash
cd /Users/sven/Desktop/MCP/.worktrees/atlas-api
python3 simple_main.py
```

**Backend Endpoints Used**:
- `GET /pipeline/runs` - Recent runs
- `POST /pipeline/run` - Upload CSV
- `GET /pipeline/status/{id}` - Run status
- `GET /quality/metrics/{id}` - Quality report
- `GET /quality/pii-report/{id}` - PII report
- `GET /connectors/` - List connectors
- `POST /connectors/` - Create connector
- `PUT /connectors/{id}` - Update connector
- `DELETE /connectors/{id}` - Delete connector
- `POST /connectors/{id}/sync` - Trigger sync
- `GET /connectors/{id}/history` - Sync history

## 🔧 Development

### Install Dependencies
```bash
npm install
```

### Start Dev Server
```bash
npm run dev
```

### Build for Production
```bash
npm run build
```

### Preview Production Build
```bash
npm run preview
```

## 📊 Data Flow

```
1. Upload CSV → 2. Process → 3. Quality Check → 4. PII Scan → 5. View Results
       ↓              ↓              ↓               ↓              ↓
   Dashboard      Pipeline     6 Dimensions    Entity Types    Reports
```

## 🎨 Design System

### Colors
- **Primary (Blue)**: Trust, professional actions
- **Success (Green)**: Quality passing, good results
- **Warning (Yellow)**: Attention needed, moderate issues
- **Danger (Red)**: Critical issues, failures
- **Neutral (Gray)**: Secondary info, inactive states

### Quality Score Colors
- 🟢 Green (≥95%): Excellent quality
- 🟡 Yellow (85-95%): Good quality
- 🔴 Red (<85%): Needs improvement

### Compliance Status
- ✅ **Compliant**: No high-risk PII, acceptable levels
- ⚠️ **Warning**: PII detected, review recommended
- 🚨 **Violation**: High-risk PII (credit cards, SSN), immediate action required

## 🚨 Troubleshooting

### Dashboard won't load
1. Check backend is running: `curl http://localhost:8000/docs`
2. Check frontend is running: Browser at http://localhost:5173
3. Check console for errors: Open browser DevTools

### No data showing
1. Upload a CSV file first (Upload page)
2. Wait for processing to complete
3. Refresh the page

### Connection test fails
1. Verify database is running
2. Check credentials are correct
3. Ensure network connectivity
4. Check firewall settings

### Charts not rendering
1. Clear browser cache
2. Refresh page
3. Check browser console for errors

## 💡 Tips

1. **Auto-refresh**: Data refreshes every 30 seconds automatically
2. **Filters**: All filters can be reset with the "Reset Filters" button
3. **Sorting**: Click table headers to sort
4. **Details**: Click any row to see detailed information
5. **Export**: Use Download buttons to export data
6. **Search**: Use search bar to quickly find datasets
7. **Confirmations**: Destructive actions require confirmation

## 📱 Mobile Support

The dashboard is fully responsive:
- **Desktop** (≥1024px): Full multi-column layout
- **Tablet** (768-1023px): 2-column grid
- **Mobile** (≥640px): Stacked single column
- **Small Mobile** (<640px): Horizontal scroll for tables

## 🔐 Security Notes

1. **Passwords**: Connector passwords are transmitted securely
2. **PII Data**: Sensitive data is highlighted but not exposed in full
3. **HTTPS**: Use HTTPS in production
4. **CORS**: Configure backend CORS for production domain

## 📚 Next Steps

1. **Upload Test Data**: Try uploading a CSV with customer data
2. **Create Connector**: Set up a database connector
3. **Review Quality**: Check quality reports and address issues
4. **Monitor PII**: Review PII detections and compliance
5. **Schedule Syncs**: Set up automated data pipelines

---

**Need Help?**: Check COMPLETION_SUMMARY.md for detailed documentation

**Enjoy using Atlas Dashboard!** 🚀
