import json
import os
import re
from datetime import datetime
from uuid import uuid4

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Finjin | Demo Banking", page_icon="💬", layout="wide")
st.title("Finjin 💬")
st.caption("Your bank, one message away · SIMULATION ONLY · No real funds or banking connections")

INITIAL_ACCOUNTS = {
    "Ayesha": {"balance": 125000.0, "card_blocked": False},
    "Ahmed": {"balance": 48000.0, "card_blocked": False},
    "Sara": {"balance": 72000.0, "card_blocked": False},
}
INITIAL_TRANSACTIONS = [
    {"id": "DEMO-001", "date": "2026-10-01", "owner": "Ayesha", "type": "expense", "category": "Groceries", "amount": 4200.0, "description": "Grocery shopping"},
    {"id": "DEMO-002", "date": "2026-10-03", "owner": "Ayesha", "type": "expense", "category": "Food", "amount": 1800.0, "description": "Restaurant"},
    {"id": "DEMO-003", "date": "2026-10-05", "owner": "Ayesha", "type": "expense", "category": "Transport", "amount": 2300.0, "description": "Fuel"},
    {"id": "DEMO-004", "date": "2026-10-07", "owner": "Ayesha", "type": "income", "category": "Salary", "amount": 95000.0, "description": "Salary received"},
]
BILLERS = {"electricity": "Electricity", "gas": "Gas", "internet": "Internet", "water": "Water"}


def init_state():
    if "accounts" not in st.session_state:
        st.session_state.accounts = json.loads(json.dumps(INITIAL_ACCOUNTS))
        st.session_state.transactions = json.loads(json.dumps(INITIAL_TRANSACTIONS))
        st.session_state.messages = []
        st.session_state.pending = None
        st.session_state.audit = []


def log(event, details):
    st.session_state.audit.append({"time": datetime.now().isoformat(timespec="seconds"), "event": event, "details": details})


def parse_command(text):
    """Deterministic mock intent parser; optional AI parsing can be added later."""
    t = text.strip().lower().replace(",", "")
    amount_match = re.search(r"(?:rs\.?|pkr|rupees?)?\s*(\d+(?:\.\d+)?)", t)
    amount = float(amount_match.group(1)) if amount_match else None
    if any(k in t for k in ["balance", "kitna paisa", "kitne paise", "kitna hai", "رقم", "بیلنس"]):
        return {"intent": "balance"}
    if any(k in t for k in ["history", "transactions", "statement", "recent", "last payments", "kharchay"]):
        return {"intent": "history"}
    if any(k in t for k in ["spending", "spent", "expenses", "expense", "kharcha", "kharch"]):
        return {"intent": "spending"}
    if any(k in t for k in ["block card", "block my card", "card block", "card band"]):
        return {"intent": "block_card"}
    if any(k in t for k in ["unblock card", "unblock my card"]):
        return {"intent": "unblock_card"}
    if any(k in t for k in ["transfer", "send", "bhejo", "bhej do", "paise bhej", "رقم بھیج"]):
        recipient = next((n for n in INITIAL_ACCOUNTS if n.lower() in t and n != st.session_state.customer), None)
        return {"intent": "transfer", "amount": amount, "recipient": recipient}
    if any(k in t for k in ["bill", "electricity", "internet", "gas", "water", "bijli"]):
        biller = next((v for k, v in BILLERS.items() if k in t), None)
        if "bijli" in t:
            biller = "Electricity"
        return {"intent": "bill", "amount": amount, "biller": biller}
    return {"intent": "unknown"}


def process(text):
    user = st.session_state.customer
    acc = st.session_state.accounts[user]
    action = parse_command(text)
    intent = action["intent"]
    if intent == "balance":
        return f"Your simulated balance is **PKR {acc['balance']:,.2f}**."
    if intent == "history":
        tx = [x for x in st.session_state.transactions if x["owner"] == user]
        if not tx:
            return "No simulated transactions found."
        return "Recent simulated transactions:\n" + "\n".join(f"- {x['date']}: {x['description']} — PKR {x['amount']:,.2f} ({x['type']})" for x in tx[-8:][::-1])
    if intent == "spending":
        tx = [x for x in st.session_state.transactions if x["owner"] == user and x["type"] == "expense"]
        total = sum(x["amount"] for x in tx)
        by_category = {}
        for x in tx:
            by_category[x["category"]] = by_category.get(x["category"], 0) + x["amount"]
        summary = "\n".join(f"- {k}: PKR {v:,.2f}" for k, v in sorted(by_category.items(), key=lambda item: -item[1]))
        return f"Based on available demo transactions, total recorded expenses are **PKR {total:,.2f}**.\n{summary}"
    if intent in ("transfer", "bill"):
        amount = action.get("amount")
        target = action.get("recipient") if intent == "transfer" else action.get("biller")
        if not amount or amount <= 0 or amount > 1_000_000:
            return "Please specify a valid amount between PKR 1 and PKR 1,000,000, e.g. 'Send Rs 5000 to Ahmed'."
        if not target:
            return "Please specify a valid recipient (Ahmed or Sara) or biller (electricity, gas, internet, water)."
        if amount > acc["balance"]:
            return "Insufficient simulated funds for this request."
        st.session_state.pending = {"intent": intent, "amount": amount, "target": target, "owner": user}
        return f"**Review simulated {'transfer' if intent == 'transfer' else 'bill payment'}:** PKR {amount:,.2f} to **{target}**. Confirm below to update demo records."
    if intent in ("block_card", "unblock_card"):
        st.session_state.pending = {"intent": intent, "owner": user}
        return f"Please confirm that you want to **{'block' if intent == 'block_card' else 'unblock'}** your simulated debit card."
    return "Try: 'What is my balance?', 'Send Rs 5000 to Ahmed', 'Pay electricity bill Rs 2500', 'Show spending', 'Show transactions', or 'Block my card'."


def confirm():
    p = st.session_state.pending
    if not p or p["owner"] != st.session_state.customer:
        return "No valid pending action."
    user = p["owner"]
    acc = st.session_state.accounts[user]
    intent = p["intent"]
    if intent in ("transfer", "bill"):
        amount = p["amount"]
        if amount <= 0 or amount > acc["balance"]:
            st.session_state.pending = None
            return "Transaction rejected: insufficient simulated funds or invalid amount."
        target = p["target"]
        if intent == "transfer" and (target not in st.session_state.accounts or target == user):
            st.session_state.pending = None
            return "Transfer rejected: invalid demo recipient."
        acc["balance"] = round(acc["balance"] - amount, 2)
        if intent == "transfer":
            st.session_state.accounts[target]["balance"] = round(st.session_state.accounts[target]["balance"] + amount, 2)
        record = {"id": f"DEMO-{uuid4().hex[:8].upper()}", "date": datetime.now().date().isoformat(), "owner": user, "type": "expense", "category": "Transfer" if intent == "transfer" else "Bills", "amount": amount, "description": f"{'Transfer to' if intent == 'transfer' else 'Bill payment to'} {target}"}
        st.session_state.transactions.append(record)
        if intent == "transfer":
            st.session_state.transactions.append({**record, "owner": target, "type": "income", "description": f"Transfer from {user}"})
        log("simulated_payment", {"id": record["id"], "owner": user, "target": target, "amount": amount})
        response = f"Demo {'transfer' if intent == 'transfer' else 'bill payment'} completed. Reference: **{record['id']}**. New simulated balance: **PKR {acc['balance']:,.2f}**."
    else:
        acc["card_blocked"] = intent == "block_card"
        log("simulated_card_status", {"owner": user, "blocked": acc["card_blocked"]})
        response = f"Simulated debit card is now **{'blocked' if acc['card_blocked'] else 'active'}**."
    st.session_state.pending = None
    return response


init_state()
with st.sidebar:
    st.header("Demo controls")
    customer = st.selectbox("Demo customer", list(INITIAL_ACCOUNTS), key="customer")
    st.info("All data is fictional. Changes are stored only in this Streamlit session.")
    if st.button("Reset demo data", use_container_width=True):
        for key in ["accounts", "transactions", "messages", "pending", "audit"]:
            st.session_state.pop(key, None)
        init_state()
        st.rerun()
    st.warning("No login or real authentication. Do not use this prototype for real banking.")

# Switching customers must never carry pending instructions or chat across accounts.
if st.session_state.get("last_customer") != customer:
    st.session_state.pending = None
    st.session_state.messages = []
    st.session_state.last_customer = customer

acc = st.session_state.accounts[customer]
col1, col2, col3 = st.columns(3)
col1.metric("Demo balance", f"PKR {acc['balance']:,.0f}")
col2.metric("Debit card", "Blocked" if acc["card_blocked"] else "Active")
col3.metric("Transactions", len([t for t in st.session_state.transactions if t["owner"] == customer]))

tab1, tab2, tab3 = st.tabs(["AI Banking Chat", "Transactions & Insights", "Audit Log"])
with tab1:
    st.subheader("Type a banking instruction")
    st.caption("Examples: What is my balance? · Send Rs 5000 to Ahmed · Pay electricity bill Rs 2500 · Show spending · Block my card")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    if st.session_state.pending:
        p = st.session_state.pending
        st.warning(f"Pending DEMO action: {p['intent']} · {p.get('target', 'debit card')} · PKR {p.get('amount', 0):,.2f}")
        c1, c2 = st.columns(2)
        if c1.button("Confirm simulated action", type="primary", use_container_width=True):
            result = confirm()
            st.session_state.messages.append({"role": "assistant", "content": result})
            st.rerun()
        if c2.button("Cancel", use_container_width=True):
            st.session_state.pending = None
            st.session_state.messages.append({"role": "assistant", "content": "Simulated action cancelled."})
            st.rerun()
    if prompt := st.chat_input("e.g. Send Rs 5000 to Ahmed", disabled=bool(st.session_state.pending)):
        st.session_state.messages.append({"role": "user", "content": prompt})
        response = process(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
with tab2:
    rows = [t for t in st.session_state.transactions if t["owner"] == customer]
    df = pd.DataFrame(rows)
    if not df.empty:
        st.dataframe(df[["date", "description", "category", "type", "amount", "id"]].iloc[::-1], hide_index=True, use_container_width=True)
        expenses = df[df["type"] == "expense"]
        if not expenses.empty:
            st.subheader("Spending by category (demo)")
            st.bar_chart(expenses.groupby("category")["amount"].sum())
    else:
        st.info("No demo transactions yet.")
with tab3:
    st.caption("Local session audit trail (not tamper-proof; demonstration only)")
    if st.session_state.audit:
        st.dataframe(pd.DataFrame(st.session_state.audit), hide_index=True, use_container_width=True)
    else:
        st.info("No actions recorded yet.")
