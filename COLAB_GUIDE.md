# Running on Google Colab

## Quick Setup

### Option A: Run Entire App in Colab (Recommended)

1. **Open Google Colab**: https://colab.research.google.com
2. **Create new notebook** → Upload `colab-setup.ipynb` from this repo
3. **Run all cells** (Colab provides free GPU/TPU automatically)
4. **Download generated blog** directly from Colab

**Advantages:**
- ✅ Free GPU/TPU access
- ✅ No local resources needed
- ✅ Works on any machine with internet
- ✅ Ollama runs on Colab's GPU

---

### Option B: Ollama on Colab + Tunnel (Access from Local Machine)

If you want to keep the Streamlit UI running locally but use Colab's compute:

1. **Create Colab notebook** with this code:
```python
# Install Ollama
!curl -fsSL https://ollama.ai/install.sh | sh

# Install ngrok for tunneling
!pip install pyngrok
from pyngrok import ngrok

# Start Ollama
import subprocess
subprocess.Popen(['ollama', 'serve'])
import time; time.sleep(3)
!ollama pull mistral

# Create ngrok tunnel
public_url = ngrok.connect(11434)
print(f"✅ Ollama available at: {public_url}")
```

2. **Copy the public URL** from ngrok output

3. **Update your `.env`** locally:
```
OLLAMA_MODEL=mistral
OLLAMA_BASE_URL=<your_ngrok_url>
```

4. **Run locally** as normal:
```bash
streamlit run app.py
```

**Why this works:**
- Colab's GPU processes the LLM
- Local machine just runs the UI
- No heavy compute needed locally

---

## Model Recommendations for Colab

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **mistral** | 7B (~4GB) | ⚡⚡⚡ Fast | ⭐⭐⭐⭐ Good | Recommended |
| **llama2** | 7B (~4GB) | ⚡⚡ Medium | ⭐⭐⭐ Fair | Solid choice |
| **neural-chat** | 7B (~4GB) | ⚡⚡⚡ Fast | ⭐⭐⭐⭐ Good | Good alternative |
| **phi** | 2.7B (~1.5GB) | ⚡⚡⚡⚡ Very Fast | ⭐⭐⭐ Fair | Quick testing |

Colab free tier: **~15GB GPU memory** → mistral fits comfortably

---

## Switching Back to Local

To return to local Ollama:
```bash
# Update .env
OLLAMA_MODEL=llama3.1
OLLAMA_BASE_URL=http://localhost:11434

# Make sure local Ollama is running
ollama serve
```

All code is compatible with both setups!
