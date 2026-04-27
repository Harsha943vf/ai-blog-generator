# Application Health Check & Maintenance Guide

## 🏥 Current Application Status

Your AI-BLOG-GENERATOR is well-structured with good error handling. However, there are **important considerations** for sustained long-term use (days, weeks, months).

---

## ⚠️ Potential Issues Over Time

### 1. Tavily API - Free Tier Limitations
**Risk Level:** 🟡 Medium

**Free tier quotas:**
- 1,000 API calls per month (~33/day)
- Rate limit: Varies by plan
- Response time: 1-2 seconds typical

**What could happen:**
- Quota exceeded error after ~30 queries
- Rate limiting if too many requests in short time
- API returns error instead of results

**Your current limits:**
- Hybrid mode: 3 sources per blog
- Open-book mode: 8 sources per blog
- If generating 5 blogs/day: ~15-40 Tavily calls = sustainable for a month

**⛔ Will it fail:** YES, after exceeding monthly quota

---

### 2. Ollama Model - Memory & Performance

**Risk Level:** 🟡 Medium

**Orca-Mini specs:**
- Memory footprint: ~4-5GB
- Your system: 8GB total RAM
- Available after OS/Streamlit: ~3-4GB free

**What could happen:**
- Memory leaks if Ollama isn't restarted
- Slowdown after 10-20 consecutive generations
- Timeout after 50+ generations without restart

**Your setup:**
- Good error handling in code
- Timeout configured: 300 seconds

**⛘ Will it degrade:** YES, over time (hours)

---

### 3. Network & Connection Issues

**Risk Level:** 🟢 Low

**Potential issues:**
- Ollama connection drops
- Tavily API timeout
- Transient network errors

**Your setup:**
- Retry logic: 3 attempts with exponential backoff ✅
- Timeout handling: 60-300 seconds ✅
- Graceful fallback: Falls back to closed_book ✅

**Will it fail:** Unlikely (handled well)

---

### 4. Cache & Storage

**Risk Level:** 🟢 Low

**Current caching:**
- In-memory cache (not persistent)
- TTL: 1 hour
- Images stored in `/images` folder

**Potential issues:**
- Generated images accumulate (10+ images = 50-100MB)
- In-memory cache resets on app restart
- Old images never deleted

**⛘ Will it cause problems:** YES (storage, cleanup)

---

### 5. Long-Running Processes

**Risk Level:** 🟡 Medium

**Current behavior:**
- Streamlit reruns entire script on each input
- No explicit state cleanup
- Session state persists in memory

**Potential issues:**
- Memory accumulation (Streamlit sessions)
- Orphaned processes
- Resource leaks over hours

**⛘ Will it degrade:** YES (after 8+ hours)

---

## ✅ Stability Recommendations

### Daily Maintenance (5 minutes)

```bash
# 1. Restart Ollama once per day (if running 8+ hours)
killall ollama
sleep 2
ollama serve &

# 2. Clear old images (keep last 20)
cd /Users/harsha/Desktop/ai-blog-generator/images
ls -t | tail -n +21 | xargs rm -f 2>/dev/null || true

# 3. Check Tavily quota usage
# Go to https://tavily.com/dashboard
# Verify: calls used < 900/1000
```

### Weekly Maintenance (30 minutes)

```bash
# 1. Restart everything
killall ollama streamlit python 2>/dev/null || true
sleep 5

# 2. Check logs for errors
grep -i error *.log | tail -20

# 3. Clear cache files
rm -f *.pyc __pycache__ -r

# 4. Verify models are available
ollama list
# Should show: orca-mini (latest)

# 5. Restart services
ollama serve &
sleep 3
streamlit run app.py
```

### Monthly Maintenance

```bash
# 1. Check Tavily API usage
# Monthly reset on 1st of month
# Plan for next month (1000 calls)

# 2. Review error logs
# Look for patterns (certain topics failing)

# 3. Update dependencies (optional)
pip install --upgrade langchain ollama tavily-python

# 4. Full cleanup
rm -rf images/* 2>/dev/null || true
```

---

## 🔧 Recommended Setup for Sustained Use

### Option 1: Hourly Auto-Restart (Recommended)

Create `restart_ollama.sh`:

```bash
#!/bin/bash
# Run this every hour to restart Ollama

OLLAMA_PID=$(pgrep -f "ollama serve" | head -1)

if [ ! -z "$OLLAMA_PID" ]; then
    uptime_seconds=$(ps -o etime= -p $OLLAMA_PID | awk '{print $NF}')
    
    # If running > 3600 seconds (1 hour), restart
    if [ "$uptime_seconds" -gt 3600 ]; then
        echo "Restarting Ollama (running for $uptime_seconds seconds)"
        kill $OLLAMA_PID
        sleep 2
        ollama serve > /tmp/ollama.log 2>&1 &
        sleep 3
    fi
fi
```

Schedule with cron:
```bash
crontab -e
# Add this line:
# 0 * * * * /Users/harsha/Desktop/ai-blog-generator/restart_ollama.sh
```

---

### Option 2: Health Check Dashboard

Create `health_check.py`:

```python
#!/usr/bin/env python3
"""System health check for AI Blog Generator"""

import os
import psutil
import requests
from datetime import datetime

def check_ollama():
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        return resp.status_code == 200
    except:
        return False

def check_tavily():
    # Check if API key is set
    key = os.getenv("TAVILY_API_KEY")
    return key and key != "your_tavily_api_key_here"

def check_memory():
    return psutil.virtual_memory().percent < 85

def check_disk():
    return psutil.disk_usage("/").percent < 90

def check_images_storage():
    images_dir = "images"
    if os.path.exists(images_dir):
        size = sum(os.path.getsize(os.path.join(images_dir, f)) 
                   for f in os.listdir(images_dir))
        return size / (1024*1024)  # MB
    return 0

print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("─" * 40)

status = {
    "Ollama": "✅" if check_ollama() else "❌",
    "Tavily API": "✅" if check_tavily() else "❌",
    "Memory": f"✅ {psutil.virtual_memory().percent:.1f}%" if check_memory() else "⚠️ HIGH",
    "Disk": f"✅ {psutil.disk_usage('/').percent:.1f}%" if check_disk() else "⚠️ FULL",
    "Images Storage": f"✅ {check_images_storage():.1f}MB"
}

for service, result in status.items():
    print(f"{service:20} {result}")

print("─" * 40)
```

Run it:
```bash
python health_check.py
```

---

## 📊 Expected Behavior Over Time

### First 24 hours
- ✅ All features working perfectly
- ✅ Tavily API: ~0-50 calls used
- ✅ Memory: Stable
- ✅ No issues expected

### Days 2-7
- ✅ Still stable
- ⚠️ Ollama may slow down after 12+ hours uptime
- ⚠️ Tavily API: ~50-300 calls used
- **Action needed:** Restart Ollama once

### Days 8-30
- ✅ Still functional
- ⚠️ May see occasional slowdowns
- ⚠️ Memory usage increasing if Streamlit running continuously
- ⚠️ Tavily API: Approaching quota (watch usage)
- **Actions needed:**
  - Restart Ollama daily
  - Clean up old images
  - Monitor Tavily quota

### Day 31+
- ⚠️ Tavily API quota resets (new month)
- Good for another month

---

## 🚨 When to Restart What

### Restart Ollama if:
- ❌ Getting "connection refused" errors
- ❌ Timeouts on consecutive requests
- ❌ Memory usage > 90%
- ✅ Generated 20+ blogs without restart

**Restart command:**
```bash
killall ollama
sleep 2
ollama serve
```

### Restart Streamlit if:
- ❌ UI becomes unresponsive
- ❌ Session state issues
- ❌ Memory leak detected
- ✅ Running > 8 hours continuously

**Restart command:**
```bash
# Kill and restart
pkill -f "streamlit run"
streamlit run app.py
```

### Monit for both:
```bash
# Using process manager (PM2 recommended)
npm install -g pm2

# Create ecosystem.config.js
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: "ollama",
      script: "ollama serve",
      restart_delay: 5000,
      max_restarts: 5,
    },
    {
      name: "blog-generator",
      script: "streamlit run app.py",
      restart_delay: 10000,
    }
  ]
};
EOF

# Start with PM2
pm2 start ecosystem.config.js
pm2 logs
```

---

## 🎯 Best Practices for Long-Term Stability

1. **Restart Ollama daily** (or after 12+ hours uptime)
2. **Monitor Tavily quota** (especially near month end)
3. **Clean up images** weekly (keep last 10-20)
4. **Check logs** for errors
5. **Monitor memory/disk** usage
6. **Restart Streamlit** if running > 8 hours

---

## 📈 Scalability

### Current Setup Handles:
- ✅ 5-10 blogs/day indefinitely
- ✅ 50+ blogs/month (with restarts)
- ✅ Tavily free tier (1000 calls/month)
- ✅ 8GB Mac (minimal other apps)

### Limitations:
- ❌ 50+ concurrent users (single process)
- ❌ 100+ blogs/month (API quota)
- ❌ High-traffic production (not scaled)

### To Scale Up:
- Add Tavily paid tier (10,000+ calls/month) = $50/month
- Deploy to cloud (AWS/GCP) = $10-50/month
- Use multi-process workers (Gunicorn)
- Cache results to database

---

## ✅ Quick Stability Checklist

**Run this every week:**

```bash
#!/bin/bash

echo "🏥 AI Blog Generator Health Check"
echo "=================================="

# 1. Check processes
echo "✓ Checking processes..."
pgrep ollama > /dev/null && echo "  Ollama: ✅" || echo "  Ollama: ❌ NOT RUNNING"

# 2. Check Ollama API
echo "✓ Testing Ollama API..."
curl -s http://localhost:11434/api/tags | jq .models[].name 2>/dev/null && echo "  API: ✅" || echo "  API: ❌"

# 3. Check disk space
echo "✓ Disk space:"
df -h / | tail -1

# 4. Check images folder
echo "✓ Images stored:"
du -sh images/ 2>/dev/null || echo "  (none)"

# 5. Check Tavily key
echo "✓ Tavily API:"
grep TAVILY_API_KEY .env | grep -q "tvly" && echo "  Configured: ✅" || echo "  Configured: ❌"

echo "=================================="
echo "Done!"
```

---

## 🎓 Summary

**Is your app stable for days?**
- ✅ **Code:** Yes, well-designed with error handling
- ⚠️ **Infrastructure:** Requires maintenance every 24-48 hours
- ⚠️ **APIs:** Tavily quota limited (1000/month)

**Recommended approach:**
1. Run for 1-2 days without issues ✅
2. Restart Ollama daily ⚠️
3. Monitor Tavily quota ⚠️
4. Clean up images weekly ⚠️
5. Restart Streamlit after 8 hours ⚠️

**With these practices:** ✅ **Runs reliably for weeks/months**

---

Need help setting up automated restarts or monitoring? Let me know! 🚀
