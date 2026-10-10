# 🔬 SciDiscovery

**AI-assisted platform** that turns research papers into structured knowledge, detects research gaps, generates testable hypotheses, and designs complete experimental protocols.

🔗 **Live Demo:** https://scientificdiscovery.vercel.app

> ⚠️ Backend on Render free tier — first request after 15 min idle takes ~30s.

---

## ✨ Features

- 📄 **Ingest** — PDF upload or pasted text
- 🧠 **Extract claims** — Groq LLM structures `(subject, relationship, property, value)`
- 🎯 **Detect gaps** — contradictions, population, geographic, temporal, methodological
- 💡 **Generate hypotheses** — H₁ + H₀ with IV/DV and quality scores
- 🧪 **Design experiments** — full protocols with statistics, timeline, ethics
- 🕸️ **Visualize** — interactive knowledge graph (React Flow)
- 📥 **Export** — download experiment plans as Markdown

---

## 🛠 Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI · SQLAlchemy · SQLite · PyMuPDF · Groq SDK · Uvicorn |
| Frontend | React 19 · Vite · TypeScript · Tailwind CSS · React Flow |
| AI | Groq (`openai/gpt-oss-120b`) |
| Deploy | Render (Docker) · Vercel |

---

## 🚀 Quick Start

```bash
git clone https://github.com/trisha-345/Scientific_Discovery.git
cd Scientific_Discovery
```

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Create .env
echo "APP_NAME=Scientific Discovery Platform" > .env
echo "GROQ_API_KEY=gsk_your_key_here" >> .env
echo "GROQ_MODEL=openai/gpt-oss-120b" >> .env

uvicorn app.main:app --reload --reload-dir app --port 8000
```

**Frontend** (new terminal):

```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev
```

→ App runs at http://localhost:5173 · API docs at http://localhost:8000/docs

---

## 🎯 Notes

- **Groq over OpenAI** — free tier, ~280 tok/s, reliable JSON output
- **Keyword-based gaps** — replaces embeddings; torch exceeds Render's 512 MB cap
- **Data is ephemeral** on free tier — resets on redeploy
- **Rate limit** — 1,000 requests/day on Groq free tier

---

## 📄 License

MIT · Trisha Honnapur