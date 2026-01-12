# Start Skill

Start the Atlas Pipeline backend and frontend services.

## When to Use
- To start development
- After system restart
- When services are not running

## Instructions

### Start Backend

```bash
cd /home/user/atlas-pipeline-v1/backend
python simple_main.py
```

Or run in background:
```bash
nohup python simple_main.py > /tmp/backend.log 2>&1 &
```

Backend will be available at: http://localhost:8000
API docs at: http://localhost:8000/docs

### Start Frontend

```bash
cd /home/user/atlas-pipeline-v1/frontend
npm run dev
```

Frontend will be available at: http://localhost:5173

### Start Both (Quick)

```bash
# Terminal 1 - Backend
cd /home/user/atlas-pipeline-v1/backend && python simple_main.py &

# Terminal 2 - Frontend
cd /home/user/atlas-pipeline-v1/frontend && npm run dev &

# Verify
sleep 5
curl -s http://localhost:8000/atlas-intelligence/health
curl -s http://localhost:5173 | head -5
```

## Port Reference
- Backend API: 8000
- Frontend Dev: 5173
- PostgreSQL: 5432
- Redis: 6379

## Troubleshooting

### Port Already in Use
```bash
# Find and kill process on port
lsof -ti :8000 | xargs kill -9
lsof -ti :5173 | xargs kill -9
```

### Backend Won't Start
Check log: `cat /tmp/backend.log`
Common causes:
- Missing dependencies (run /setup)
- Port already in use
- Import errors (check for typos)

### Frontend Won't Start
```bash
cd frontend
rm -rf node_modules
npm install
npm run dev
```
