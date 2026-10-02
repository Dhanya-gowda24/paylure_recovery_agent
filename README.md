# 💸 RecoverAI: Paylure Agent

An AI agent that finds why payments are failing, picks a recovery action for each cause,
and asks a human before high-value actions. Built for the Razorpay AI Buildathon (Track 3: AI Revenue Recovery).

## What it does
- Analyzes failed payments and groups them by cause (error code, payment method, bank)
- Detects patterns such as a likely bank outage (e.g. 40% of failures are UPI timeouts on one bank)
- Recommends a recovery action per cause: smart retry, re-payment link, alternative method
- Estimates recoverable revenue
- Runs low-risk actions automatically; **requires human approval** for groups losing more than ₹5 lakh
- Gemini decides which tools to call (function calling) and writes a plain-English report
- Falls back to an offline rule-based mode if the LLM is unavailable

## Tech stack
Python · Pandas · Streamlit · Google Gemini (tool calling)

## Run it
```bash
pip install -r requirements.txt
python generate_data.py          # creates fake failed_payments.csv
# optional, enables the live AI agent:
#   Windows PowerShell:  $env:GEMINI_API_KEY="your_key"
#   Mac/Linux:           export GEMINI_API_KEY="your_key"
python -m streamlit run app.py
```

## Files
| File | Purpose |
|---|---|
| `generate_data.py` | Creates 800 simulated failed payments |
| `tools.py` | Tools the agent calls: group failures, suggest action, estimate recovery, send message (simulated) |
| `agent.py` | Gemini agent with automatic offline fallback |
| `app.py` | Streamlit dashboard with approval buttons |
| `diagnose.py` | Checks the Gemini connection step by step |

## Important notes
- All data is **simulated**. Recovery percentages are assumptions in `tools.py`, not real bank statistics.
- Customer messages are **simulated** (printed, not sent).
- Never commit your API key. Use environment variables or Streamlit Secrets.
