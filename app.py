"""dashboard Run: streamlit run app.py"""
import pandas as pd
import streamlit as st
import tools as T
from agent import run_agent

st.set_page_config(page_title="Payment Recovery Agent", page_icon="💸", layout="wide")
st.title("💸 AI Payment Failure Recovery Agent")
st.caption("Finds why payments fail, picks a recovery action, and asks a human before big-money actions.")

LIMIT = 500000  # actions on groups losing more than this need human approval

df = T.get_failed_payments()
groups = T.group_by_failure_reason(df)
for g in groups:
    g["label"] = f"{g['error_code']} · {g['method']}/{g['bank']}"
    g["action"] = T.suggest_action(g["error_code"])["action"]
    g["recoverable"] = T.estimate_recovery(g)
    g["needs_approval"] = g["lost_amount"] > LIMIT

if "approved" not in st.session_state:
    st.session_state.approved = set()

# money recovered = auto-approved small groups + human-approved big groups
recovered = sum(g["recoverable"] for g in groups
                if (not g["needs_approval"]) or g["label"] in st.session_state.approved)
potential = sum(g["recoverable"] for g in groups)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Failed payments", f"{len(df):,}")
c2.metric("Revenue lost", f"₹{df.amount.sum():,}")
c3.metric("Recoverable (potential)", f"₹{potential:,.0f}")
c4.metric("Recovery actions executed", f"₹{recovered:,.0f}")

st.subheader("Where the money is being lost")
chart = pd.DataFrame({"Lost ₹": [g["lost_amount"] for g in groups]},
                     index=[g["label"] for g in groups])
st.bar_chart(chart)

st.subheader("Recovery plan")
for g in groups:
    a, b, c = st.columns([3, 4, 2])
    a.markdown(f"**{g['label']}**  \n{g['count']} fails · {g['share_pct']}% · lost ₹{g['lost_amount']:,}")
    b.markdown(f"{g['action']}  \nRecoverable ≈ **₹{g['recoverable']:,.0f}**")
    if not g["needs_approval"]:
        c.success("Auto-executed")
    elif g["label"] in st.session_state.approved:
        c.success("Approved by human ✅")
    else:
        if c.button("Approve action", key=g["label"]):
            st.session_state.approved.add(g["label"])
            st.rerun()
    st.divider()

st.subheader("🤖 AI agent report")
if st.button("Run AI agent"):
    with st.spinner("Agent is investigating..."):
        st.session_state.report = run_agent()
r = st.session_state.get("report")
if r:
    {"online": st.success, "saved": st.info}.get(r["mode"], st.warning)(f"{r['mode'].upper()} — {r['note']}")
    st.markdown(r["text"])
