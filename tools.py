
import pandas as pd

# Chance that we can recover a payment, and the best action, for each error type
PLAYBOOK = {
    "UPI_TIMEOUT":        (0.60, "Auto-retry in 30 minutes; alert team if one bank dominates"),
    "INVALID_CVV":        (0.70, "Send customer a link to re-enter card details"),
    "CARD_DECLINED":      (0.30, "Offer alternative payment method (UPI / another card)"),
    "INSUFFICIENT_FUNDS": (0.25, "Send reminder after 24h with a payment link"),
    "BANK_SERVER_DOWN":   (0.50, "Retry after bank recovers; suggest UPI meanwhile"),
    "OTP_FAILED":         (0.55, "Send new payment link with fresh OTP"),
    "NETWORK_ERROR":      (0.65, "Auto-retry immediately"),
}

def get_failed_payments(path="failed_payments.csv") -> pd.DataFrame:
    return pd.read_csv(path)

def group_by_failure_reason(df: pd.DataFrame) -> list[dict]:
    """Group failures by (error_code, method, bank) and rank by money lost."""
    g = (df.groupby(["error_code", "method", "bank"])
           .agg(count=("payment_id", "count"), lost_amount=("amount", "sum"))
           .reset_index()
           .sort_values("lost_amount", ascending=False))
    g["share_pct"] = (g["count"] / len(df) * 100).round(1)
    return g.to_dict("records")

def suggest_action(error_code: str) -> dict:
    prob, action = PLAYBOOK.get(error_code, (0.10, "Escalate to human engineer"))
    return {"error_code": error_code, "recovery_chance": prob, "action": action}

def estimate_recovery(group: dict) -> float:
    prob = suggest_action(group["error_code"])["recovery_chance"]
    return round(group["lost_amount"] * prob, 2)

def send_recovery_message(customer_id: str, message: str) -> str:
    """Simulated for the demo. Real version would call SMS/email/WhatsApp."""
    return f"[SIMULATED] Sent to {customer_id}: {message}"
