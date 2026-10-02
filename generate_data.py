
import random
import pandas as pd
from datetime import datetime, timedelta

random.seed(42)

# (method, bank, error_code, weight)  -> weights make some problems bigger than others
SCENARIOS = [
    ("UPI",        "HDFC", "UPI_TIMEOUT",        40), 
    ("UPI",        "SBI",  "UPI_TIMEOUT",         4),
    ("Card",       "ICICI","INVALID_CVV",        14),
    ("Card",       "AXIS", "CARD_DECLINED",      10),
    ("Card",       "SBI",  "INSUFFICIENT_FUNDS", 10),
    ("Netbanking", "SBI",  "BANK_SERVER_DOWN",    8),
    ("Card",       "HDFC", "OTP_FAILED",          7),
    ("Wallet",     "PAYTM","NETWORK_ERROR",       7),
]

def make_payments(n=800):
    weights = [s[3] for s in SCENARIOS]
    start = datetime.now() - timedelta(hours=24)
    rows = []
    for i in range(n):
        method, bank, code, _ = random.choices(SCENARIOS, weights=weights)[0]
        rows.append({
            "payment_id": f"pay_{1000 + i}",
            "timestamp": (start + timedelta(minutes=random.randint(0, 1440))).strftime("%Y-%m-%d %H:%M"),
            "customer_id": f"cust_{random.randint(1, 300)}",
            "amount": random.choice([199, 499, 999, 1499, 2999, 4999, 9999, 24999]),
            "method": method,
            "bank": bank,
            "error_code": code,
        })
    return pd.DataFrame(rows)

if __name__ == "__main__":
    df = make_payments()
    df.to_csv("failed_payments.csv", index=False)
    print(f"Created failed_payments.csv with {len(df)} rows")
    print(df.head())
