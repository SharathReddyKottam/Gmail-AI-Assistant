import os, re, time, pickle, subprocess
import pandas as pd
import streamlit as st
import gspread
import plotly.express as px
from google.oauth2.credentials import Credentials

# ---------- Page Config ----------
st.set_page_config(page_title="📬 Gmail AI Dashboard", layout="wide")

px.defaults.template = "plotly_dark"
px.defaults.color_discrete_sequence = px.colors.qualitative.Pastel

st.markdown("""
<style>
body {background-color:#0E1117;}
.main {background-color:#0E1117;padding:2rem;border-radius:12px;}
h1,h2,h3,p,span{color:#EAEAEA !important;}
div[data-testid="stMetricValue"]{font-size:1.5rem;}
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
col_title, col_btn = st.columns([6,1])
with col_title:
    st.title("📬 Gmail AI Control Center")
    st.caption("Private, AI-powered insights from your Gmail — by Sharath Reddy Kottam")
with col_btn:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

REFRESH_INTERVAL = 60
st.caption(f"⏱️ Auto-refreshes every {REFRESH_INTERVAL}s")

# ---------- Auth ----------
if not os.path.exists("token.json"):
    st.error("⚠️ token.json not found. Run summarize_emails.py first.")
    st.stop()

with open("token.json","rb") as t: creds=pickle.load(t)
gc = gspread.authorize(creds)
SHEET_ID="1mTotStPswtCYRAfsp54G70Kn4pybgEOHSdcOHa4ig00"

try:
    sheet=gc.open_by_key(SHEET_ID).sheet1
    data=pd.DataFrame(sheet.get_all_records())
except Exception as e:
    st.error(f"❌ Could not load Google Sheet: {e}")
    st.stop()

if data.empty:
    st.info("📭 No data yet. Run summarize_emails.py to populate.")
    st.stop()

# ---------- Clean + Convert ----------
def clean_sender(s):
    if not isinstance(s,str): return "Unknown"
    return re.sub(r"<.*?>","",s).strip()
data["SenderName"]=data["Sender"].apply(clean_sender)

# Ensure date parsed
if "Date" in data.columns:
    data["Date"]=pd.to_datetime(data["Date"],errors="coerce")

# ---------- Priority Ranking (local Ollama) ----------
def get_priority(summary):
    if not summary.strip(): return 3
    prompt=f"Rate this email importance from 1 (low) to 5 (high):\n{summary}\nAnswer only the number."
    try:
        r=subprocess.run(["ollama","run","mistral",prompt],capture_output=True,text=True,timeout=30)
        out=r.stdout.strip()
        val=int(re.findall(r"[1-5]",out)[0]) if re.findall(r"[1-5]",out) else 3
        return val
    except Exception: return 3

if "Priority" not in data.columns:
    with st.spinner("Scoring priorities via Ollama..."):
        data["Priority"]=data["Summary"].apply(get_priority)

# ---------- AI Digest ----------
def ai_digest(rows):
    joined="\n".join(f"- {s}" for s in rows)
    prompt=f"Summarize these emails into 4-6 bullet points (concise daily digest):\n{joined}"
    try:
        r=subprocess.run(["ollama","run","mistral",prompt],
                         capture_output=True,text=True,timeout=60)
        return r.stdout.strip() or "(no digest returned)"
    except Exception as e:
        return f"(Digest error: {e})"

st.markdown("## 🧾 Today's Digest")
digest=ai_digest(data["Summary"].tail(10))
st.markdown(digest)

# ---------- Overview Metrics ----------
st.markdown("### 📈 Overview")
c1,c2,c3,c4=st.columns(4)
with c1: st.metric("Total Emails",len(data))
with c2: st.metric("Unique Senders",data["SenderName"].nunique())
with c3: st.metric("Categories",data["Category"].nunique())
with c4: st.metric("Avg Priority",round(data["Priority"].mean(),1))
st.markdown("---")

# ---------- Trend Over Time ----------
if "Date" in data.columns:
    daily=data.groupby(data["Date"].dt.date).size().reset_index(name="Count")
    fig_t=px.line(daily,x="Date",y="Count",markers=True,
                  title="📆 Emails Over Time")
    fig_t.update_layout(margin=dict(t=60,b=40))
    st.plotly_chart(fig_t,use_container_width=True,key="trend_chart")

# ---------- Category Distribution ----------
st.subheader("🏷️ Category Distribution")
cat=data["Category"].value_counts().reset_index()
cat.columns=["Category","Count"]
fig_c=px.bar(cat,x="Category",y="Count",color="Category",text="Count",
             title="Email Categories")
fig_c.update_traces(textposition="outside")
fig_c.update_layout(yaxis_title="Emails",xaxis_title=None,showlegend=False,
                    margin=dict(t=60,b=40))
st.plotly_chart(fig_c,use_container_width=True,key="cat_chart")

# ---------- Top Senders ----------
st.subheader("📨 Top Senders")
data["SenderShort"]=data["SenderName"].apply(lambda x: x[:20]+"..." if len(x)>20 else x)
top=data["SenderShort"].value_counts().head(10).reset_index()
top.columns=["Sender","Count"]
fig_s=px.bar(top,x="Sender",y="Count",color="Sender",text="Count",
             title="Top 10 Senders")
fig_s.update_traces(textposition="outside")
fig_s.update_layout(xaxis_tickangle=15,showlegend=False,margin=dict(t=60,b=60))
st.plotly_chart(fig_s,use_container_width=True,key="send_chart")

# ---------- Natural-Language Query ----------
st.markdown("---")
st.markdown("### 💬 Ask Your Inbox")
query=st.text_input("Type a query (e.g. 'show job emails from last week'):")

def nl_filter(q,df):
    if not q: return df
    q=q.lower()
    if "job" in q: df=df[df["Category"].str.contains("job",case=False)]
    if "event" in q: df=df[df["Category"].str.contains("event",case=False)]
    if "finance" in q or "invoice" in q: df=df[df["Category"].str.contains("fin",case=False)]
    return df

filtered=nl_filter(query,data)

# ---------- Data Table ----------
st.subheader("📋 Email Summaries")
category_filter=st.selectbox("🔍 Filter by Category",["All"]+sorted(data["Category"].unique()))
if category_filter!="All": filtered=filtered[filtered["Category"]==category_filter]

st.dataframe(filtered[["Date","SenderName","Subject","Summary","Category","Priority"]],
             use_container_width=True)

# ---------- Auto-refresh ----------
time.sleep(REFRESH_INTERVAL)
st.rerun()
