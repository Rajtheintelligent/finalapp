# .streamlit/secrets.toml

[gcp_service_account]
# ... your full service account JSON inline here ...

[google]
register_sheet_url = "https://docs.google.com/spreadsheets/d/REGISTER_SHEET_ID/edit"

[google.question_sheet_urls]
maths   = "https://docs.google.com/spreadsheets/d/QUESTIONS_MATH_ID/edit"
english = "https://docs.google.com/spreadsheets/d/QUESTIONS_ENG_ID/edit"
science = "https://docs.google.com/spreadsheets/d/QUESTIONS_SCI_ID/edit"

[google.response_sheet_urls]
maths   = "https://docs.google.com/spreadsheets/d/RESP_MATH_ID/edit"
english = "https://docs.google.com/spreadsheets/d/RESP_ENG_ID/edit"
science = "https://docs.google.com/spreadsheets/d/RESP_SCI_ID/edit"

[telegram]
bot_token = "123456789:ABC_your_bot_token"
