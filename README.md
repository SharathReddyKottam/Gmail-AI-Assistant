# 📬 Gmail AI Assistant

A privacy-focused **AI-powered Gmail dashboard** that summarizes, categorizes, and visualizes your inbox — built with **Python, Ollama, and Streamlit**.

---

## 🚀 Features

- 🤖 **Local AI Summaries** using Ollama (no API key required)
- 🧾 **AI Digest** — daily summary of new emails
- ⭐ **Priority Scoring** (1–5 importance ranking)
- 🏷️ **Category Classification** (Jobs, Finance, Events, etc.)
- 💬 **Natural-Language Query Bar** — filter with plain text
- 📈 **Email Trends Over Time** (Plotly charts)
- 🔄 **Inline Refresh** & Auto-update every 60 seconds
- 🔐 100% local processing — privacy-first

---

## 🧠 Tech Stack

| Component | Technology |
|------------|-------------|
| Backend | Python 3.13 |
| AI | Ollama (Mistral) |
| Frontend | Streamlit + Plotly |
| Data | Google Sheets API |
| Mail Access | Gmail API |
| Auth | OAuth 2.0 |

---

## ⚙️ Setup

```bash
# 1. Clone the repo
git clone https://github.com/SharathReddyKottam/Gmail-AI-Assistant.git
cd Gmail-AI-Assistant

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your Google API credentials
# (credentials.json should be downloaded from Google Cloud Console)

# 5. Run the summarizer
python summarize_emails.py

# 6. Run the dashboard
streamlit run dashboard.py
