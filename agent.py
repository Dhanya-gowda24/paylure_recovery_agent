import os
import tools as T

DF = T.get_failed_payments()

# ---- Tools the LLM can call (simple inputs/outputs only) ----
def get_failure_summary() -> list:
    """Returns failed-payment groups (error_code, method, bank, count, lost_amount, share_pct), biggest money loss first."""
    return T.group_by_failure_reason(DF)

def get_recovery_action(error_code: str) -> dict:
    """Returns the recommended action and recovery chance (0-1) for a given error_code."""
    return T.suggest_action(error_code)

def send_recovery_message(customer_id: str, message: str) -> str:
    """Sends a recovery message to a customer (simulated)."""
    return T.send_recovery_message(customer_id, message)

SYSTEM = """You are a Payment Failure Recovery agent for a payments company.
Your job: find why payments are failing, decide the best recovery action per problem group, and estimate recovered revenue.
Steps: 1) call get_failure_summary. 2) For the top 4 groups call get_recovery_action.
3) Spot any bank/method that dominates failures and flag it as a likely outage.
4) Send ONE sample recovery message for the top customer-fixable issue using send_recovery_message (use customer_id cust_1).
Finish with a short report: top causes (with % and rupee loss), action per cause, estimated recoverable revenue
(lost_amount x recovery_chance), and any item that needs HUMAN approval (amount > 5 lakh). Use plain simple English."""

def candidate_models(client) -> list:
    """Ordered list of models to try: stable 'flash' first, preview/experimental last."""
    if os.environ.get("GEMINI_MODEL"):
        return [os.environ["GEMINI_MODEL"]]
    bad = ("image", "tts", "live", "audio", "embed", "robotics", "computer", "omni")
    stable, risky = [], []
    for m in client.models.list():
        n = m.name.replace("models/", "")
        actions = getattr(m, "supported_actions", None) or ["generateContent"]
        if "flash" not in n or any(x in n for x in bad) or "generateContent" not in actions:
            continue
        (risky if any(x in n for x in ("preview", "exp", "lite")) else stable).append(n)
    names = sorted(stable, reverse=True) + sorted(risky, reverse=True)
    if not names:
        raise RuntimeError("No flash model available for this key")
    return names[:5]

def run_online(api_key: str) -> tuple:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=api_key)
    errors = []
    for model in candidate_models(client):  # if one model has no quota, try the next
        try:
            resp = client.models.generate_content(
                model=model,
                contents="Analyze today's failed payments and produce the recovery plan.",
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM,
                    tools=[get_failure_summary, get_recovery_action, send_recovery_message],
                ),
            )
            return resp.text, model
        except Exception as e:
            errors.append(f"{model}: {str(e)[:90]}")
            if not any(k in str(e) for k in ("429", "404", "RESOURCE_EXHAUSTED", "NOT_FOUND", "503")):
                raise
    raise RuntimeError("All models failed -> " + " | ".join(errors))

def run_offline() -> str:
    lines, total = ["(OFFLINE MODE: rule-based, no LLM)\n"], 0
    for g in T.group_by_failure_reason(DF)[:4]:
        a, rec = T.suggest_action(g["error_code"]), T.estimate_recovery(g)
        total += rec
        flag = "  ** NEEDS HUMAN APPROVAL **" if g["lost_amount"] > 500000 else ""
        lines.append(f"- {g['error_code']} on {g['method']}/{g['bank']}: {g['share_pct']}% of failures, "
                     f"lost ₹{g['lost_amount']:,}. Action: {a['action']}. Recoverable ≈ ₹{rec:,.0f}.{flag}")
    lines.append(f"\nEstimated recoverable revenue (top 4): ₹{total:,.0f}")
    return "\n".join(lines)

CACHE_FILE = "last_online_report.json"

def save_cache(text: str, model: str):
    import json, datetime
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({"text": text, "model": model,
                   "saved_at": datetime.datetime.now().strftime("%d %b %Y, %H:%M")}, f)

def load_cache():
    import json
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def fallback(reason: str) -> dict:
    """If a saved real Gemini report exists, show it (clearly labelled). Otherwise use offline rules."""
    c = load_cache()
    if c:
        return {"mode": "saved", "text": c["text"],
                "note": f"Live call unavailable ({reason}). Showing the last REAL Gemini report, "
                        f"saved {c['saved_at']} (model: {c['model']})."}
    return {"mode": "offline", "note": reason, "text": run_offline()}

def run_agent() -> dict:
    import time
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return fallback("GEMINI_API_KEY not set")
    last_err = ""
    for attempt in range(1, 4):  # retry up to 3 times: connection drops are often temporary
        try:
            text, model = run_online(key)
            save_cache(text, model)
            return {"mode": "online", "note": f"Model: {model} (attempt {attempt})", "text": text}
        except Exception as e:
            last_err = str(e)[:200]
            if any(k in last_err for k in ("404", "429", "API key", "403", "All models failed")):
                break  # retrying will not help for these
            time.sleep(2 * attempt)
    return fallback(last_err)

if __name__ == "__main__":
    r = run_agent()
    print(f"[{r['mode'].upper()}] {r['note']}\n")
    print(r["text"])
