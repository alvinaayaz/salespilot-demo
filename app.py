import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from storage import get_supabase_client, load_or_seed_leads, insert_lead, update_lead, delete_lead
from presentation import safe_csv_value, safe_html_text

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

# Persistent mode activates only after Streamlit secrets are configured.
try:
    supabase_url = st.secrets.get("SUPABASE_URL", "")
    supabase_anon_key = st.secrets.get("SUPABASE_ANON_KEY", "")
except Exception:
    supabase_url = ""
    supabase_anon_key = ""

PERSISTENT_MODE = bool(supabase_url and supabase_anon_key)
if PERSISTENT_MODE:
    if "supabase_client" not in st.session_state:
        try:
            st.session_state.supabase_client = get_supabase_client(supabase_url, supabase_anon_key)
        except Exception as exc:
            st.error("SalesPilot could not connect to its database. Please try again later.")
            st.stop()
    if "supabase_user_id" not in st.session_state:
        st.session_state.supabase_user_id = None

    if not st.session_state.supabase_user_id:
        st.title("Welcome to SalesPilot")
        st.caption("Sign in to your sales workspace, or create a free account.")
        login_tab, signup_tab = st.tabs(["Sign in", "Create account"])
        with login_tab:
            with st.form("salespilot_signin"):
                login_email = st.text_input("Email address")
                login_password = st.text_input("Password", type="password")
                login_submit = st.form_submit_button("Sign in", type="primary", use_container_width=True)
            if login_submit:
                try:
                    auth_result = st.session_state.supabase_client.auth.sign_in_with_password({"email": login_email.strip(), "password": login_password})
                    st.session_state.supabase_user_id = auth_result.user.id
                    st.session_state.supabase_user_email = auth_result.user.email
                    st.rerun()
                except Exception:
                    st.error("Sign-in failed. Check your email and password.")
        with signup_tab:
            with st.form("salespilot_signup"):
                signup_email = st.text_input("Email address", key="signup_email")
                signup_password = st.text_input("Password (at least 8 characters)", type="password", key="signup_password")
                signup_submit = st.form_submit_button("Create account", type="primary", use_container_width=True)
            if signup_submit:
                if len(signup_password) < 8:
                    st.error("Use a password with at least 8 characters.")
                else:
                    try:
                        signup_result = st.session_state.supabase_client.auth.sign_up({"email": signup_email.strip(), "password": signup_password})
                        if signup_result.session:
                            st.session_state.supabase_user_id = signup_result.user.id
                            st.session_state.supabase_user_email = signup_result.user.email
                            st.rerun()
                        else:
                            st.success("Account created. Check your email to confirm it, then sign in.")
                    except Exception:
                        st.error("Account creation failed. This email may already be registered.")
        st.stop()

    if "leads" not in st.session_state:
        try:
            st.session_state.leads = load_or_seed_leads(
                st.session_state.supabase_client,
                st.session_state.supabase_user_id,
                [],
            )
        except Exception:
            st.error("Your workspace could not be loaded. Please refresh and try again.")
            st.stop()
else:
    if "leads" not in st.session_state:
        st.session_state.leads = [dict(x) for x in INITIAL_LEADS]

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--ink:#18231f;--muted:#56645d;--line:#e2e8e3;--paper:#ffffff;--canvas:#f6f8f6;--green:#24634b;--green-soft:#edf5ef;--rust:#c56b43}
.stApp{background:var(--canvas)!important;color:var(--ink);font-family:'Manrope',sans-serif!important;font-size:15px}
.block-container{max-width:1360px;padding:2rem 2.8rem 4rem}
h1,h2,h3{color:var(--ink);letter-spacing:-.035em;font-family:'Space Grotesk','Manrope',sans-serif!important}
h1{font-family:'Space Grotesk','Manrope',sans-serif!important;font-size:3.65rem!important;font-weight:700!important;line-height:1.06!important;margin:0}
h2{font-family:'Space Grotesk','Manrope',sans-serif!important;font-size:1.4rem!important;font-weight:700!important;letter-spacing:-.03em}
h3{font-family:'Space Grotesk','Manrope',sans-serif!important;font-size:1.12rem!important;font-weight:700!important}
p,[data-testid=stMarkdownContainer] p{line-height:1.7;font-size:1rem;color:#26352c}
[data-testid=stCaptionContainer],.stCaption{color:#4d5b52!important;font-size:.95rem!important;line-height:1.55}
label,[data-testid=stWidgetLabel] p{color:#172a20!important;font-size:1.05rem!important;font-weight:700!important}
[data-testid=stMetric]{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:1.2rem 1.25rem;box-shadow:0 2px 8px rgba(25,45,32,.04)}
[data-testid=stMetricLabel]{color:#35483c!important;font-size:1rem!important;font-weight:700!important}
[data-testid=stMetricValue]{color:var(--ink)!important;font-family:'Space Grotesk','Manrope',sans-serif!important;font-size:2.4rem!important;font-weight:700!important}
[data-testid=stVerticalBlockBorderWrapper]{background:var(--paper);border:1px solid var(--line);border-radius:16px;padding:.85rem;box-shadow:0 5px 20px rgba(24,35,31,.045)}
[data-testid=stTextInput] input,[data-testid=stSelectbox] div[data-baseweb=select],[data-testid=stTextArea] textarea{border:1.5px solid #87998c!important;border-radius:8px!important;background:#fff!important;color:#17231c!important;font-size:1rem!important}
[data-testid=stTextArea] textarea{line-height:1.65}
input::placeholder,textarea::placeholder{color:#526258!important;opacity:1!important}
.stButton>button,.stDownloadButton>button{border-radius:8px;min-height:2.9rem;font-size:1.05rem;font-weight:700;border:1.5px solid #87998c;background:#fff;color:#17231c}
.stButton>button[kind=primary],.stDownloadButton>button[kind=primary]{background:var(--green);border-color:var(--green);color:#fff}
.stButton>button[kind=primary]:hover,.stDownloadButton>button[kind=primary]:hover{background:#183e2c;border-color:#183e2c;color:#fff}
[data-testid=stDataFrame]{border:1px solid var(--line);border-radius:9px;overflow:hidden}
[data-testid=stAlert]{background:#e5efe7!important;border:1px solid #b8cbbb!important;border-radius:9px;color:#14231b!important}
[data-testid=stAlert] *{color:#14231b!important}
[data-testid="stBaseButton-primary"],[data-testid="stDownloadButton"] button[kind="primary"],.stButton button[kind="primary"]{background:#1e5138!important;border:1.5px solid #1e5138!important;color:#ffffff!important}
[data-testid="stBaseButton-primary"] *,[data-testid="stDownloadButton"] button[kind="primary"] *,.stButton button[kind="primary"] *{color:#ffffff!important}
[data-testid="stBaseButton-primary"]:hover,.stButton button[kind="primary"]:hover{background:#173f2c!important;border-color:#173f2c!important}
[data-testid="stSelectbox"] [data-baseweb="select"]>div{background:#ffffff!important;border-color:#87998c!important;color:#17231c!important}
[data-testid="stSelectbox"] [data-baseweb="select"] *{color:#17231c!important}
[data-testid=stExpander]{border-color:var(--line)!important}
hr{border-color:var(--line);margin:1.7rem 0}
div[data-testid=stHorizontalBlock]{gap:1.1rem}
button,[role=button]{font-size:1rem}
@media(max-width:700px){.block-container{padding:1rem .9rem 3rem}h1{font-size:2.8rem!important}[data-testid=stMetricValue]{font-size:1.8rem!important}}
</style>""", unsafe_allow_html=True)

# A quiet, editorial workspace: clear hierarchy over dashboard clutter
if PERSISTENT_MODE:
    account_col, logout_col = st.columns([5, 1])
    account_col.caption(f"Signed in as {st.session_state.get('supabase_user_email', 'your account')}")
    if logout_col.button("Sign out", use_container_width=True):
        st.session_state.supabase_client.auth.sign_out()
        st.session_state.supabase_user_id = None
        st.session_state.pop("supabase_user_email", None)
        st.session_state.pop("leads", None)
        st.rerun()

workspace_label = "WORKSPACE" if PERSISTENT_MODE else "PREVIEW WORKSPACE"
workspace_status = "YOUR ACCOUNT · YOUR PIPELINE" if PERSISTENT_MODE else "PREVIEW DATA · SESSION ONLY"
st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;padding:4px 0 18px;border-bottom:1px solid #e5e8e1">
  <div style="display:flex;align-items:center;gap:11px">
    <div style="width:34px;height:34px;background:#24634b;color:#ffffff;display:grid;place-items:center;font-family:'Space Grotesk',sans-serif;font-size:19px;font-weight:700;border-radius:10px">S</div>
    <span style="font-size:16px;font-weight:800;letter-spacing:-.6px;color:#18231f">salespilot</span>
    <span style="font-size:12px;letter-spacing:.8px;color:#46564b;margin-left:5px">{workspace_label}</span>
  </div>
  <div style="font-size:13px;color:#46564b;letter-spacing:.3px">{workspace_status}</div>
</div>
""", unsafe_allow_html=True)

hero_l, hero_r = st.columns([1.7, 1], gap="large")
with hero_l:
    st.markdown("<div style='margin-top:35px;font-size:12px;letter-spacing:1.5px;font-weight:800;color:#24634b;margin-bottom:15px'>YOUR SALES OVERVIEW &nbsp; / &nbsp; 01</div>", unsafe_allow_html=True)
    st.markdown("<h1>Your sales,<br><span style='color:#24634b'>under control.</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:16px;max-width:510px;margin-top:17px;line-height:1.75;color:#56645d'>A clearer view of your prospects, priorities, and next steps — all in one workspace.</p>", unsafe_allow_html=True)
with hero_r:
    follow_up_count = sum(1 for item in st.session_state.leads if item.get("status") == "Follow-up")
    st.markdown(f"""<div style="margin-top:39px;background:#24634b;border-radius:16px;padding:24px 25px;color:#ffffff;min-height:160px"><div style="font-size:13px;letter-spacing:1.3px;color:#f3f7f3;font-weight:700">A NOTE FOR TODAY</div><div style="font-family:Space Grotesk,Manrope,sans-serif;font-size:29px;font-weight:700;line-height:1.12;margin-top:16px">Follow up with<br>intention.</div><div style="font-size:14px;color:#f0f5f1;margin-top:13px;line-height:1.55">{follow_up_count} conversations are waiting for a thoughtful next touch.</div></div>""", unsafe_allow_html=True)

leads = st.session_state.leads
total = len(leads)
hot = sum(score_lead(l) >= 75 for l in leads)
follow = sum(l["status"] == "Follow-up" for l in leads)
qualified = sum(l["status"] == "Qualified" for l in leads)

st.markdown("<div style='font-size:13px;letter-spacing:1px;font-weight:800;color:#46564b;margin:28px 0 12px'>YOUR PIPELINE</div>", unsafe_allow_html=True)
m1,m2,m3,m4 = st.columns(4)
m1.metric("Total prospects", total, help="All prospects currently in this workspace")
m2.metric("High-priority leads", hot)
m3.metric("Need follow-up", follow)
m4.metric("Qualified", qualified)

st.markdown("<div style='font-size:11px;letter-spacing:1.2px;font-weight:800;color:#35483c;margin:30px 0 14px'>PIPELINE AT A GLANCE</div>", unsafe_allow_html=True)
statuses = ["New","Contacted","Qualified","Follow-up","Won","Lost"]
stage_counts = pd.Series([l["status"] for l in leads]).value_counts()
priority_levels = ["High","Medium","Low"]
priority_counts = {p: sum(priority(score_lead(l)) == p for l in leads) for p in priority_levels}

def render_bars(rows, bar_color):
    max_count = max([count for _, count in rows] + [1])
    pieces = [
        "<div style='display:flex;flex-direction:column;gap:17px;padding:10px 2px 5px'>"
    ]
    for label, count in rows:
        width = round((count / max_count) * 100) if count else 0
        pieces.append(
            "<div style='display:grid;grid-template-columns:94px minmax(70px,1fr) 34px;align-items:center;gap:13px'>"
            f"<span style='font-size:14px;font-weight:600;color:#26382d'>{label}</span>"
            "<div style='height:13px;background:#edf1ed;border:1px solid #dce5dd;border-radius:20px;overflow:hidden'>"
            f"<div style='height:100%;width:{width}%;min-width:{'4px' if count else '0'};background:{bar_color};border-radius:20px'></div></div>"
            f"<span style='font-size:14px;font-weight:700;color:#172a20;text-align:right;background:#f1f5f1;border-radius:7px;padding:3px 5px'>{count}</span></div>"
        )
    pieces.append("</div>")
    return "".join(pieces)

left, right = st.columns([1.5,1], gap="large")
with left:
    with st.container(border=True):
        st.subheader("Lead pipeline")
        st.caption("How many prospects are at each stage")
        stage_rows = [(s, int(stage_counts.get(s, 0))) for s in statuses if int(stage_counts.get(s, 0)) > 0]
        if stage_rows:
            st.markdown(render_bars(stage_rows, "#24543d"), unsafe_allow_html=True)
        else:
            st.caption("Your pipeline is empty.")
with right:
    with st.container(border=True):
        st.subheader("Priority snapshot")
        st.caption("Where your attention may be needed")
        priority_rows = [(p, priority_counts[p]) for p in priority_levels]
        st.markdown(render_bars(priority_rows, "#9a593e"), unsafe_allow_html=True)

st.markdown("<div style='font-size:11px;letter-spacing:1.2px;font-weight:800;color:#35483c;margin:30px 0 14px'>YOUR PROSPECTS</div>", unsafe_allow_html=True)
with st.container(border=True):
    st.subheader("Prospect inbox")
    st.caption("Search your pipeline and filter prospects by stage or priority.")
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
        styled_table = (
            table.style
            .hide(axis="index")
            .set_properties(**{
                "background-color": "#ffffff",
                "color": "#172a20",
                "border-color": "#e2e8e3",
                "font-size": "14px",
                "padding": "12px 10px",
                "text-align": "left",
                "white-space": "nowrap",
            })
            .set_table_styles([
                {"selector": "table", "props": [("width", "100%"), ("border-collapse", "separate"), ("border-spacing", "0"), ("border", "1px solid #d8e1da"), ("border-radius", "10px"), ("overflow", "hidden")]},
                {"selector": "thead th", "props": [("background-color", "#e8efe9"), ("color", "#172a20"), ("font-weight", "700"), ("font-size", "13px"), ("padding", "12px 10px"), ("border-bottom", "1px solid #cbd8ce")]},
                {"selector": "tbody tr:nth-child(even) td", "props": [("background-color", "#f6f9f6")]},
                {"selector": "tbody tr:hover td", "props": [("background-color", "#edf4ee")]},
                {"selector": "tbody td", "props": [("border-bottom", "1px solid #e2e8e3")]},
            ])
            .format(escape="html")
        )
        st.table(styled_table)
    else:
        st.info("No leads match these filters.")

if total == 0:
    with st.container(border=True):
        st.subheader("Your workspace is ready")
        st.write("Add your first prospect to start organizing opportunities, tracking follow-ups, and preparing thoughtful replies.")
        st.caption("Your workspace starts empty. Only prospects you add will appear here.")

with st.expander("Add a prospect", expanded=total == 0):
    st.caption("Create a prospect record. Name, company, and need are required.")
    with st.form("add_lead_form", clear_on_submit=True):
        add_a, add_b = st.columns(2)
        new_name = add_a.text_input("Contact name *", placeholder="Jordan Lee")
        new_company = add_b.text_input("Company *", placeholder="Company name")
        add_c, add_d = st.columns(2)
        new_role = add_c.text_input("Role", placeholder="Founder, Sales Manager…")
        new_email = add_d.text_input("Email", placeholder="name@company.com")
        new_source = st.selectbox("Lead source", ["Website inquiry", "LinkedIn", "Referral", "Cold outreach", "Other"])
        new_need = st.text_area("What are they looking for? *", placeholder="Describe their goal, challenge, or request.")
        new_notes = st.text_area("Notes", placeholder="Useful context for your next conversation.")
        new_status = st.selectbox("Initial stage", ["New", "Contacted", "Qualified", "Follow-up"])
        add_submitted = st.form_submit_button("Add prospect", type="primary", use_container_width=True)
        if add_submitted:
            clean_name = new_name.strip()
            clean_company = new_company.strip()
            clean_email = new_email.strip()
            if not clean_name or not clean_company or not new_need.strip():
                st.error("Please complete the contact name, company, and need.")
            elif clean_email and ("@" not in clean_email or "." not in clean_email.rsplit("@", 1)[-1]):
                st.error("Enter a valid email address, or leave it blank.")
            elif any(x["name"].casefold() == clean_name.casefold() and x["company"].casefold() == clean_company.casefold() for x in st.session_state.leads):
                st.error("This contact already exists for that company.")
            else:
                new_lead = {
                    "name": clean_name,
                    "company": clean_company,
                    "role": new_role.strip() or "Not specified",
                    "source": new_source,
                    "email": clean_email,
                    "need": new_need.strip(),
                    "notes": new_notes.strip(),
                    "status": new_status,
                    "last_touch": "Added just now",
                }
                if PERSISTENT_MODE:
                    try:
                        new_lead = insert_lead(st.session_state.supabase_client, st.session_state.supabase_user_id, new_lead)
                    except Exception:
                        st.error("The prospect could not be saved. Please try again.")
                        st.stop()
                st.session_state.leads.append(new_lead)
                st.success(f"{clean_name} was added to your pipeline.")
                st.rerun()

if leads:
    with st.container(border=True):
      st.subheader("Lead desk")
      st.caption("Open a prospect to review details, update their stage, or prepare a reply.")
      names = [f'{l["name"]} — {l["company"]}' for l in leads]
      selected = st.selectbox("Choose a prospect", names)
      idx = names.index(selected)
      lead = leads[idx]
      sc = score_lead(lead)
      safe_name = safe_html_text(lead["name"])
      safe_role = safe_html_text(lead["role"])
      safe_company = safe_html_text(lead["company"])
      st.markdown(f"<div style='background:#f7f8fc;border:1px solid #eceef4;border-radius:14px;padding:18px 20px;margin:8px 0 16px'><div style='font:800 21px Manrope,sans-serif;color:#172033'>{safe_name}</div><div style='color:#758096;font-size:13px;margin-top:4px'>{safe_role} · {safe_company}</div></div>", unsafe_allow_html=True)
      a,b,c = st.columns(3)
      a.metric("Lead score",f"{sc}/100")
      b.metric("Priority",priority(sc))
      c.metric("Pipeline stage",lead["status"])
      with st.expander("Edit prospect details"):
          with st.form("edit_lead_form"):
              edit_a, edit_b = st.columns(2)
              edit_name = edit_a.text_input("Contact name", value=lead["name"])
              edit_company = edit_b.text_input("Company", value=lead["company"])
              edit_c, edit_d = st.columns(2)
              edit_role = edit_c.text_input("Role", value=lead["role"])
              edit_email = edit_d.text_input("Email", value=lead["email"])
              source_options = ["Website inquiry", "LinkedIn", "Referral", "Cold outreach", "Other"]
              edit_source = st.selectbox("Lead source", source_options, index=source_options.index(lead["source"]) if lead["source"] in source_options else 4)
              edit_need = st.text_area("Need", value=lead["need"])
              edit_notes = st.text_area("Notes", value=lead["notes"])
              stage_options = ["New", "Contacted", "Qualified", "Follow-up", "Won", "Lost"]
              edit_status = st.selectbox("Pipeline stage", stage_options, index=stage_options.index(lead["status"]))
              saved = st.form_submit_button("Save changes", type="primary", use_container_width=True)
              if saved:
                  clean_edit_name = edit_name.strip()
                  clean_edit_company = edit_company.strip()
                  clean_edit_email = edit_email.strip()
                  duplicate = any(i != idx and x["name"].casefold() == clean_edit_name.casefold() and x["company"].casefold() == clean_edit_company.casefold() for i, x in enumerate(st.session_state.leads))
                  if not clean_edit_name or not clean_edit_company or not edit_need.strip():
                      st.error("Name, company, and need cannot be blank.")
                  elif clean_edit_email and ("@" not in clean_edit_email or "." not in clean_edit_email.rsplit("@", 1)[-1]):
                      st.error("Enter a valid email address, or leave it blank.")
                  elif duplicate:
                      st.error("Another prospect already has this name and company.")
                  else:
                      updated_lead = {
                          **st.session_state.leads[idx],
                          "name": clean_edit_name, "company": clean_edit_company,
                          "role": edit_role.strip() or "Not specified", "email": clean_edit_email,
                          "source": edit_source, "need": edit_need.strip(),
                          "notes": edit_notes.strip(), "status": edit_status,
                      }
                      if PERSISTENT_MODE:
                          try:
                              update_lead(st.session_state.supabase_client, st.session_state.supabase_user_id, updated_lead)
                          except Exception:
                              st.error("Changes could not be saved. Please try again.")
                              st.stop()
                      st.session_state.leads[idx] = updated_lead
                      st.success("Prospect details saved.")
                      st.rerun()
      st.markdown("**Signal / need**")
      st.write(lead["need"])
      st.markdown("**Context**")
      st.write(lead["notes"])
      st.caption(f"Last touch · {lead['last_touch']}")
      st.markdown("#### Suggested next step")
      def render_readable_notice(message):
          st.markdown(
              f"<div style='background:#e7f0e8;border:1px solid #b8cbbb;border-left:5px solid #285b45;border-radius:9px;padding:14px 16px;color:#14231b;font-size:15px;font-weight:600;line-height:1.55'>{message}</div>",
              unsafe_allow_html=True,
          )

      if priority(sc) == "High":
          render_readable_notice("Prioritize a personal response today. Confirm their use case and offer a relevant next step.")
      elif priority(sc) == "Medium":
          render_readable_notice("Send a short, helpful note. Ask one clear question to learn more.")
      else:
          render_readable_notice("Keep this lead warm. Share a useful resource or revisit when you have a stronger signal.")
      st.markdown("#### Reply draft")
      draft = st.text_area("Draft (edit before use)", value=draft_reply(lead), height=145)
      st.caption("Draft only. Nothing is sent from SalesPilot.")
      col1,col2 = st.columns([1,1])
      with col1:
          if st.button("Mark as contacted", use_container_width=True, type="primary"):
              updated_lead = {**st.session_state.leads[idx], "status": "Contacted", "last_touch": "Just now"}
              if PERSISTENT_MODE:
                  try:
                      update_lead(st.session_state.supabase_client, st.session_state.supabase_user_id, updated_lead)
                  except Exception:
                      st.error("The stage change could not be saved.")
                      st.stop()
              st.session_state.leads[idx] = updated_lead
              st.rerun()
      with col2:
          if st.button("Set follow-up", use_container_width=True):
              updated_lead = {**st.session_state.leads[idx], "status": "Follow-up", "last_touch": "Just now"}
              if PERSISTENT_MODE:
                  try:
                      update_lead(st.session_state.supabase_client, st.session_state.supabase_user_id, updated_lead)
                  except Exception:
                      st.error("The follow-up change could not be saved.")
                      st.stop()
              st.session_state.leads[idx] = updated_lead
              st.rerun()

      with st.expander("Remove this prospect"):
          st.warning("This permanently removes the selected prospect from your workspace. This cannot be undone.")
          confirm_delete = st.checkbox(
              f"I understand — permanently remove {lead['name']} from my pipeline.",
              key=f"confirm_delete_{lead.get('id', idx)}",
          )
          if st.button("Delete prospect", disabled=not confirm_delete, key=f"delete_lead_{lead.get('id', idx)}"):
              if PERSISTENT_MODE:
                  try:
                      delete_lead(
                          st.session_state.supabase_client,
                          st.session_state.supabase_user_id,
                          lead["id"],
                      )
                  except Exception:
                      st.error("The prospect could not be deleted. Please try again.")
                      st.stop()
              st.session_state.leads.pop(idx)
              st.success("Prospect removed from your pipeline.")
              st.rerun()

with st.container(border=True):
    st.subheader("Export your pipeline")
    st.caption("Download a copy of the prospects in this workspace.")
    export = pd.DataFrame([{**l,"score":score_lead(l),"priority":priority(score_lead(l))} for l in st.session_state.leads])
    export = export.apply(lambda column: column.map(safe_csv_value))
    st.download_button("Download lead list as CSV", export.to_csv(index=False).encode("utf-8"), "salespilot_demo_leads.csv", "text/csv", type="primary")
    with st.expander("About SalesPilot"):
        st.write("SalesPilot helps you organize prospects, understand lead signals, track pipeline stages, and prepare outreach drafts. Lead scores and suggested next steps are generated using transparent rules, not an AI model. SalesPilot does not send messages or connect to external CRMs.")
        st.write("All names, organizations, and contact details are fictional placeholders.")
