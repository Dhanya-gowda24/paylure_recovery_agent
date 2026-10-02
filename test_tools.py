from generate_data import make_payments
from tools import *

df = get_failed_payments()
print(f"Total failed: {len(df)} | Total lost: ₹{df.amount.sum():,}\n")
total = 0
for g in group_by_failure_reason(df)[:5]:
    rec = estimate_recovery(g)
    total += rec
    print(f"{g['error_code']:<20} {g['method']:<11} {g['bank']:<6} {g['count']:>4} fails  {g['share_pct']:>5}%  lost ₹{g['lost_amount']:>9,}  recoverable ₹{rec:>10,.0f}")
    print(f"   -> {suggest_action(g['error_code'])['action']}")
print(f"\nTop-5 recoverable: ₹{total:,.0f}")
