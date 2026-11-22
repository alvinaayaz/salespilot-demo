import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="SalesPilot | Sales Workspace", page_icon="🎯", layout="wide")

# Demo-only records: fictional people and companies.
INITIAL_LEADS = [
    {"name":"Maya Chen","company":"Northstar Studio","role":"Founder","source":"Website inquiry","email":"maya@example.test","need":"Looking for a way to organize inbound sales inquiries.","notes":"Asked about a simple CRM workflow.","status":"New","last_touch":"Today"},
    {"name":"Omar Rahman","company":"BrightPath Media","role":"Operations Lead","source":"LinkedIn","email":"omar@example.test","need":"Interested in automating repetitive follow-ups.","notes":"Downloaded the automation checklist.","status":"Contacted","last_touch":"Yesterday"},
    {"name":"Sofia Patel","company":"Kite & Co.","role":"Sales Manager","source":"Referral","email":"sofia@example.test","need":"Wants better visibility into lead priorities.","notes":"Suggested a short product walkthrough.","status":"Qualified","last_touch":"2 days ago"},
    {"name":"Ethan Brooks","company":"LoopWorks","role":"Owner","source":"Cold outreach","email":"ethan@example.test","need":"Asked for pricing but hasn't replied.","notes":"Keep next message concise and low-pressure.","status":"Follow-up","last_touch":"5 days ago"},
    {"name":"Zara Ali","company":"Evergreen Labs","role":"Growth","source":"Website inquiry","email":"zara@example.test","need":"Comparing options for team workflow.","notes":"Requested examples for a small team.","status":"New","last_touch":"Today"},
    {"name":"Leo Martin","company":"Cobalt Creative","role":"Director","source":"LinkedIn","email":"leo@example.test","need":"No clear use case yet.","notes":"Open with discovery question.","status":"New","last_touch":"1 week ago"},
    {"name":"Nina Flores","company":"CloudNine Retail","role":"Customer Experience","source":"Referral","email":"nina@example.test","need":"Reduce time spent on manual lead tracking.","notes":"Follow-up was delayed.","status":"Follow-up","last_touch":"6 days ago"},
]

def score_lead(lead):
    score = 35
    text = (lead["need"] + " " + lead["notes"]).lower()
    for term, points in [("pricing",18),("looking for",14),("interested",14),("automating",15),("asked",12),("reduce",12),("requested",10),("comparing",8),("workflow",8),("inquiry",10)]:
        if term in text: score += points
    score += {"Qualified":15,"Contacted":5,"Follow-up":8,"New":0}.get(lead["status"],0)
    return min(score, 100)

def priority(score):
    return "High" if score >= 75 else "Medium" if score >= 55 else "Low"

def draft_reply(lead):
    need = lead["need"].strip()
    if lead["status"] == "Follow-up":
        return f"Hi {lead['name'].split()[0]}, just checking back on this. Is improving your process for {need.lower()} still a priority? Happy to share a few ideas if useful."
    if "pricing" in need.lower():
        return f"Hi {lead['name'].split()[0]}, thanks for your interest. I can share a straightforward overview of pricing and what is included. What would be most useful for your team?"
    return f"Hi {lead['name'].split()[0]}, thanks for reaching out. I saw that you're looking at {need.lower()} Would it be helpful if I shared a couple of practical options based on your workflow?"

if "leads" not in st.session_state:
    st.session_state.leads = [dict(x) for x in INITIAL_LEADS]

st.markdown("""
<style>
.block-container{padding-top:1.7rem;max-width:1400px}
[data-testid="stMetric"]{background:rgba(120,120,120,.07);padding:14px 16px;border-radius:12px;border:1px solid rgba(120,120,120,.12)}
div[data-testid="stDataFrame"]{border-radius:12px}
</style>
""", unsafe_allow_html=True)

st.title("🎯 SalesPilot")
st.caption("A lightweight sales workspace • Demo data only • No messages are sent")
st.markdown("**Turn a messy lead list into your next clear action.**")

leads = st.session_state.leads
total = len(leads)
hot = sum(score_lead(l) >= 75 for l in leads)
follow = sum(l["status"] == "Follow-up" for l in leads)
qualified = sum(l["status"] == "Qualified" for l in leads)

m1,m2,m3,m4 = st.columns(4)
m1.metric("Total prospects", total)
m2.metric("High-priority leads", hot)
m3.metric("Need follow-up", follow)
m4.metric("Qualified", qualified)

st.divider()
left, right = st.columns([1.8,1])
with left:
    st.subheader("Lead pipeline")
    statuses = ["New","Contacted","Qualified","Follow-up","Won","Lost"]
    counts = pd.Series([l["status"] for l in leads]).value_counts()
    pipe = pd.DataFrame({"Stage":statuses,"Leads":[int(counts.get(s,0)) for s in statuses]})
    st.bar_chart(pipe.set_index("Stage"))
with right:
    st.subheader("Priority snapshot")
    snap = pd.DataFrame({"Priority":["High","Medium","Low"],"Count":[sum(priority(score_lead(l))==p for l in leads) for p in ["High","Medium","Low"]]})
    st.bar_chart(snap.set_index("Priority"))

st.divider()
st.subheader("Prospect inbox")
c1,c2,c3 = st.columns([1.5,1,1])
search = c1.text_input("Search leads", placeholder="Name, company, or need")
stage_filter = c2.selectbox("Pipeline stage",["All"]+["New","Contacted","Qualified","Follow-up","Won","Lost"])
priority_filter = c3.selectbox("Priority",["All","High","Medium","Low"])
view = []
for lead in leads:
    s = score_lead(lead)
    if search and search.lower() not in (lead["name"]+" "+lead["company"]+" "+lead["need"]).lower(): continue
    if stage_filter != "All" and lead["status"] != stage_filter: continue
    if priority_filter != "All" and priority(s) != priority_filter: continue
    view.append({**lead,"Score":s,"Priority":priority(s)})
if view:
    table = pd.DataFrame(view)[["name","company","role","source","status","Score","Priority","last_touch"]]
    table.columns = ["Contact","Company","Role","Source","Stage","Score","Priority","Last touch"]
    st.dataframe(table, use_container_width=True, hide_index=True)
else:
    st.info("No leads match these filters.")

st.divider()
st.subheader("Lead desk")
names = [f'{l["name"]} — {l["company"]}' for l in leads]
selected = st.selectbox("Choose a prospect", names)
idx = names.index(selected)
lead = leads[idx]
sc = score_lead(lead)
a,b,c = st.columns([2,1,1])
a.markdown(f"### {lead['name']}  
**{lead['role']} · {lead['company']}**")
b.metric("Lead score",f"{sc}/100")
c.metric("Priority",priority(sc))
st.write("**Signal / need**",lead["need"])
st.write("**Context**",lead["notes"])
st.write("**Last touch**",lead["last_touch"])

st.markdown("#### Suggested next step")
if priority(sc) == "High":
    st.info("Prioritize a personal response today. Confirm their use case and offer a relevant next step.")
elif priority(sc) == "Medium":
    st.info("Send a short, helpful note. Ask one clear question to learn more.")
else:
    st.info("Keep this lead warm. Share a useful resource or revisit when you have a stronger signal.")

st.markdown("#### Reply draft")
draft = st.text_area("Draft (edit before use)", value=draft_reply(lead), height=145)
st.caption("This is an editable suggestion. SalesPilot does not send emails, texts, or calls.")
col1,col2 = st.columns([1,1])
with col1:
    if st.button("Mark as contacted", use_container_width=True):
        st.session_state.leads[idx]["status"] = "Contacted"
        st.session_state.leads[idx]["last_touch"] = "Just now"
        st.rerun()
with col2:
    if st.button("Set follow-up", use_container_width=True):
        st.session_state.leads[idx]["status"] = "Follow-up"
        st.session_state.leads[idx]["last_touch"] = "Just now"
        st.rerun()

st.divider()
st.subheader("Export")
export = pd.DataFrame([{**l,"score":score_lead(l),"priority":priority(score_lead(l))} for l in st.session_state.leads])
st.download_button("Download lead list as CSV", export.to_csv(index=False).encode("utf-8"), "salespilot_demo_leads.csv", "text/csv")
with st.expander("About this demo"):
    st.write("SalesPilot is a portfolio prototype using local rule-based lead scoring and draft suggestions. It does not connect to a CRM, external AI provider, email, phone, or real customer database.")
    st.write("All names, organizations, and contact details are fictional placeholders.")
