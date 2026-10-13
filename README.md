# Finjin — Mock Banking MVP

A Streamlit demo of conversational banking using **fictional data only**. No real bank integrations, real payments, or authentication.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

## Demo commands

- `What is my balance?`
- `Send Rs 5000 to Ahmed`
- `Pay electricity bill Rs 2500`
- `Show transactions`
- `Show spending`
- `Block my card`

Payments and card actions require a confirmation click. Use the sidebar to switch between fictional users or reset data.

## Important limitations

This is a **rule-based natural-language prototype**, not yet an LLM-powered AI agent. The next phase will add tool-calling with a model and secure backend validation. Data is stored in Streamlit session state and can be reset; there is no durable database, authentication, or real banking connection. Never enter real financial information.
