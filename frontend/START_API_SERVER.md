# Start Your Conversation API Server

## 🚀 Quick Start

### 1. Copy API Server to Your Main Directory
```bash
cp /tmp/temp-seven/scripts/conversation_api.py /Users/sven/Desktop/MCP/seven-ultimate-productivity/scripts/
```

### 2. Start the API Server
```bash
cd /Users/sven/Desktop/MCP/seven-ultimate-productivity
python scripts/conversation_api.py
```

### 3. Get Your Local IP Address
```bash
# On macOS
ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1

# Should show something like: 192.168.1.100
```

### 4. Update GitHub Actions with Your IP

Edit `.github/workflows/REAL-CONTEXT.yml` and replace:
```yaml
API_URL="http://YOUR_LOCAL_IP:8080/search"
```

With your actual IP:
```yaml
API_URL="http://192.168.1.100:8080/search"
```

### 5. Test the API Locally
```bash
# Test basic connection
curl "http://localhost:8080/"

# Test search
curl "http://localhost:8080/search?query=productivity&limit=3"

# Test stats
curl "http://localhost:8080/stats"
```

## 📋 Expected Output

When the API server starts, you should see:
```
🚀 Starting Seven Conversation Search API...
📍 Database: /Users/sven/Desktop/MCP/seven-ultimate-productivity/data/seven.db
🌐 API will be available at: http://localhost:8080

Endpoints:
  GET /search?query=your+search&limit=5
  GET /stats
  GET /conversation/{id}
```

## 🎯 How It Works

1. **GitHub Actions** detects new issues
2. **Extracts keywords** from issue title/body  
3. **Calls your local API** at `http://YOUR_IP:8080/search`
4. **Gets real conversation context** from your 25M+ word database
5. **Adds enhanced comment** with actual relevant conversations

## ⚠️ Important Notes

- **Keep the API running** for GitHub Actions to work
- **Use your LOCAL network IP** (not localhost) for GitHub to reach it
- **Firewall**: You might need to allow port 8080
- **Router**: GitHub Actions calls from external IP, router must allow port 8080

## 🔧 Troubleshooting

**API not accessible from GitHub?**
- Check firewall settings
- Use actual IP address, not localhost
- Ensure port 8080 is open

**Database not found?**
- Verify path in conversation_api.py matches your database location
- Run search_conversations.py locally first to confirm database works

**No search results?**
- Test API locally: `curl "http://localhost:8080/search?query=test"`
- Check database has data: `curl "http://localhost:8080/stats"`

## 🎉 Success Test

Create a new GitHub issue after setting this up. You should see:
- ✅ Automatic comment with real conversation context
- ✅ Relevant snippets from your ChatGPT/Claude history
- ✅ Enhanced Claude Code integration instructions

**Your automation will finally have REAL context from your 25M+ word database!**