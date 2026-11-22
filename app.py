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
    first_name = lead["name"].split()[0]
    need = lead["need"].strip().lower()

    if lead["status"] == "Follow-up":
        return (
            f"Hi {first_name}, just checking back on my earlier note. "
            "Is this still something you're exploring? Happy to share a few "
            "practical ideas if that would be useful."
        )

    if "pricing" in need:
        return (
            f"Hi {first_name}, thanks for your interest. I can share a clear "
            "overview of the pricing and what's included. Is there a particular "
            "feature or team need you'd like me to focus on?"
        )

    if "organize inbound sales inquiries" in need:
        context = "organizing your inbound sales inquiries"
    elif "automating repetitive follow-ups" in need:
        context = "automating repetitive follow-ups"
    elif "better visibility into lead priorities" in need:
        context = "getting a clearer view of lead priorities"
    elif "comparing options for team workflow" in need:
        context = "finding a workflow that fits your team"
    elif "reduce time spent on manual lead tracking" in need:
        context = "spending less time on manual lead tracking"
    else:
        context = "making your sales workflow easier to manage"

    return (
        f"Hi {first_name}, thanks for reaching out. I saw you're exploring "
        f"{context}. Would it be helpful if I shared a couple of practical "
        "ideas based on how your team works today?"
    )

if "leads" not in st.session_state:
    st.session_state.leads = [dict(x) for x in INITIAL_LEADS]

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Instrument+Serif:ital@0;1&display=swap');
:root{--ink:#202923;--muted:#778078;--line:#e5e8e1;--paper:#fffefa;--canvas:#f6f6f1;--green:#285b45;--green-soft:#edf3ee;--rust:#bd654b}
.stApp{background:var(--canvas);color:var(--ink);font-family:'DM Sans',sans-serif}
.block-container{max-width:1190px;padding:1.5rem 2.4rem 4rem}
h1,h2,h3{color:var(--ink);letter-spacing:-.025em}
h1{font-family:'Instrument Serif',serif!important;font-size:3.25rem!important;font-weight:400!important;line-height:1.02!important;margin:0}
h2{font-family:'DM Sans',sans-serif!important;font-size:1.12rem!important;font-weight:700!important;letter-spacing:-.03em}
h3{font-family:'DM Sans',sans-serif!important;font-size:1rem!important;font-weight:700!important}
p{line-height:1.65}
[data-testid=stCaptionContainer]{color:var(--muted);font-size:.82rem}
[data-testid=stMetric]{background:var(--paper);border:1px solid var(--line);border-radius:11px;padding:1.05rem 1.15rem;box-shadow:none}
[data-testid=stMetricLabel]{color:var(--muted);font-size:.77rem;font-weight:600}
[data-testid=stMetricValue]{color:var(--ink);font-family:'Instrument Serif',serif;font-size:2.35rem;font-weight:400}
[data-testid=stVerticalBlockBorderWrapper]{background:var(--paper);border:1px solid var(--line);border-radius:13px;padding:.45rem;box-shadow:none}
[data-testid=stTextInput] input,[data-testid=stSelectbox] div[data-baseweb=select],[data-testid=stTextArea] textarea{border:1px solid #dfe4dc!important;border-radius:7px!important;background:#fffefa!important}
[data-testid=stTextArea] textarea{line-height:1.65}
.stButton>button,.stDownloadButton>button{border-radius:7px;min-height:2.65rem;font-weight:600;border:1px solid #dce2da;background:#fffefa;color:var(--ink)}
.stButton>button[kind=primary],.stDownloadButton>button[kind=primary]{background:var(--green);border-color:var(--green);color:#fff}
.stButton>button[kind=primary]:hover,.stDownloadButton>button[kind=primary]:hover{background:#1d4936;border-color:#1d4936}
[data-testid=stDataFrame]{border:1px solid var(--line);border-radius:8px;overflow:hidden}
[data-testid=stAlert]{background:var(--green-soft);border:1px solid #dce8de;border-radius:8px;color:var(--ink)}
hr{border-color:var(--line);margin:1.55rem 0}
div[data-testid=stHorizontalBlock]{gap:1rem}
@media(max-width:700px){.block-container{padding:1rem .85rem 3rem}h1{font-size:2.55rem!important}}
</style>""", unsafe_allow_html=True)

# A quiet, editorial workspace: clear hierarchy over dashboard clutter
st.markdown("""
<div style="display:flex;align-items:center;justify-content:space-between;padding:4px 0 18px;border-bottom:1px solid #e5e8e1">
  <div style="display:flex;align-items:center;gap:11px">
    <div style="width:31px;height:31px;background:#285b45;color:#fffefa;display:grid;place-items:center;font-family:'Instrument Serif',serif;font-size:23px;border-radius:7px">s</div>
    <span style="font-size:15px;font-weight:700;letter-spacing:-.4px;color:#202923">salespilot</span>
    <span style="font-size:10px;letter-spacing:1.1px;color:#778078;margin-left:5px">PRIVATE WORKSPACE</span>
  </div>
  <div style="font-size:11px;color:#778078;letter-spacing:.4px">SAMPLE DATA &nbsp;·&nbsp; NO OUTBOUND MESSAGES</div>
</div>
""", unsafe_allow_html=True)

hero_l, hero_r = st.columns([1.7, 1], gap="large")
with hero_l:
    st.markdown("<div style='margin-top:35px;font-size:10px;letter-spacing:2px;font-weight:700;color:#285b45;margin-bottom:13px'>YOUR SALES OVERVIEW &nbsp; / &nbsp; 01</div>", unsafe_allow_html=True)
    st.markdown("<h1>Make room for<br><em style='color:#285b45'>good conversations.</em></h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#778078;font-size:14px;max-width:440px;margin-top:13px'>A considered view of your prospects, priorities and the next small step that moves a relationship forward.</p>", unsafe_allow_html=True)
with hero_r:
    st.markdown(f"<div style='margin-top:39px;background:#285b45;border-radius:10px;padding:22px 23px;color:#fffefa;min-height:160px'><div style='font-size:10px;letter-spacing:1.7px;color:#c7d8cc;font-weight:700'>A NOTE FOR TODAY</div><div style='font-family:Instrument Serif,serif;font-size:29px;line-height:1.08;margin-top:16px'>Follow up with<br>intention.</div><div style='font-size:12px;color:#d5e0d7;margin-top:13px'>{sum(l["status"] == "Follow-up" for l in st.session_state.leads)} conversations are waiting for a thoughtful next touch.</div></div>", unsafe_allow_html=True)

leads = st.session_state.leads
total = len(leads)
hot = sum(score_lead(l) >= 75 for l in leads)
follow = sum(l["status"] == "Follow-up" for l in leads)
qualified = sum(l["status"] == "Qualified" for l in leads)

st.markdown("<div style='font-size:11px;letter-spacing:1.2px;font-weight:800;color:#8a93a5;margin:28px 0 12px'>THE PIPELINE, AT A GLANCE</div>", unsafe_allow_html=True)
m1,m2,m3,m4 = st.columns(4)
m1.metric("Total prospects", total, help="All sample prospects in this workspace")
m2.metric("High-priority leads", hot)
m3.metric("Need follow-up", follow)
m4.metric("Qualified", qualified)

st.markdown("<div style='font-size:11px;letter-spacing:1.2px;font-weight:800;color:#8a93a5;margin:28px 0 12px'>WHERE THINGS STAND</div>", unsafe_allow_html=True)
left, right = st.columns([1.65,1], gap="large")
with left:
    with st.container(border=True):
        st.subheader("Lead pipeline")
        st.caption("Prospects grouped by their current stage")
        statuses = ["New","Contacted","Qualified","Follow-up","Won","Lost"]
        counts = pd.Series([l["status"] for l in leads]).value_counts()
        pipe = pd.DataFrame({"Stage":statuses,"Leads":[int(counts.get(s,0)) for s in statuses]})
        st.bar_chart(pipe.set_index("Stage"), color="#635bdb")
with right:
    with st.container(border=True):
        st.subheader("Priority snapshot")
        st.caption("Where your attention may be needed")
        snap = pd.DataFrame({"Priority":["High","Medium","Low"],"Count":[sum(priority(score_lead(l))==p for l in leads) for p in ["High","Medium","Low"]]})
        st.bar_chart(snap.set_index("Priority"), color="#8a83ed")

st.markdown("<div style='font-size:11px;letter-spacing:1.2px;font-weight:800;color:#8a93a5;margin:28px 0 12px'>THE PEOPLE BEHIND THE NUMBERS</div>", unsafe_allow_html=True)
with st.container(border=True):
    st.subheader("Prospect inbox")
    st.caption("Search, filter and review the people in your pipeline.")
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

with st.container(border=True):
    st.subheader("Lead desk")
    st.caption("Review a prospect and decide on the next best action.")
    names = [f'{l["name"]} — {l["company"]}' for l in leads]
    selected = st.selectbox("Choose a prospect", names)
    idx = names.index(selected)
    lead = leads[idx]
    sc = score_lead(lead)
    st.markdown(f"<div style='background:#f7f8fc;border:1px solid #eceef4;border-radius:14px;padding:18px 20px;margin:8px 0 16px'><div style='font:800 21px Manrope,sans-serif;color:#172033'>{lead['name']}</div><div style='color:#758096;font-size:13px;margin-top:4px'>{lead['role']} · {lead['company']}</div></div>", unsafe_allow_html=True)
    a,b,c = st.columns(3)
    a.metric("Lead score",f"{sc}/100")
    b.metric("Priority",priority(sc))
    c.metric("Pipeline stage",lead["status"])
    st.markdown("**Signal / need**")
    st.write(lead["need"])
    st.markdown("**Context**")
    st.write(lead["notes"])
    st.caption(f"Last touch · {lead['last_touch']}")
    st.markdown("#### Suggested next step")
    if priority(sc) == "High":
        st.info("Prioritize a personal response today. Confirm their use case and offer a relevant next step.")
    elif priority(sc) == "Medium":
        st.info("Send a short, helpful note. Ask one clear question to learn more.")
    else:
        st.info("Keep this lead warm. Share a useful resource or revisit when you have a stronger signal.")
    st.markdown("#### Reply draft")
    draft = st.text_area("Draft (edit before use)", value=draft_reply(lead), height=145)
    st.caption("An editable suggestion only. SalesPilot never sends emails, texts, or calls.")
    col1,col2 = st.columns([1,1])
    with col1:
        if st.button("Mark as contacted", use_container_width=True, type="primary"):
            st.session_state.leads[idx]["status"] = "Contacted"
            st.session_state.leads[idx]["last_touch"] = "Just now"
            st.rerun()
    with col2:
        if st.button("Set follow-up", use_container_width=True):
            st.session_state.leads[idx]["status"] = "Follow-up"
            st.session_state.leads[idx]["last_touch"] = "Just now"
            st.rerun()

with st.container(border=True):
    st.subheader("Export your pipeline")
    st.caption("Take your sample lead list with you as a CSV file.")
    export = pd.DataFrame([{**l,"score":score_lead(l),"priority":priority(score_lead(l))} for l in st.session_state.leads])
    st.download_button("Download lead list as CSV", export.to_csv(index=False).encode("utf-8"), "salespilot_demo_leads.csv", "text/csv", type="primary")
    with st.expander("About this demo"):
        st.write("SalesPilot is a portfolio prototype using local rule-based lead scoring and draft suggestions. It does not connect to a CRM, external AI provider, email, phone, or real customer database.")
        st.write("All names, organizations, and contact details are fictional placeholders.")
