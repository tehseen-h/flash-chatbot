# Install dependencies before running:
# pip install streamlit langchain langchain-google-genai python-dotenv gspread oauth2client

import streamlit as st
import json
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# Step 1: Load Gemini API key from Streamlit secrets
api_key = st.secrets["GOOGLE_API_KEY"]

# Step 2: Google Sheets setup using Streamlit secrets
def init_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Load credentials from Streamlit secrets
    creds_dict = st.secrets["gcp_service_account"]
    creds_json = json.loads(json.dumps(creds_dict))  # Convert TOML → dict
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    
    client = gspread.authorize(creds)
    sheet = client.open("ChatLogs prompts").sheet1
    return sheet

sheet = init_sheet()

# Step 3: Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.7,
    google_api_key=api_key
)

# Step 4: Prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are a helpful, conversational assistant. The user is named {user_name} and works as a {user_work}. "
     "When replying, use their name naturally in the flow of conversation — not always at the start. "
     "Use analogies or examples from their profession ({user_work}) *only if* they help make your answer clearer. "
     "Be informative, concise, and human-like.\n"
     "Here's the recent conversation:\n{chat_history}"),
    
    ("human", "{question}")
])

# Step 5: Streamlit UI setup
st.set_page_config(page_title="⚡︎ Flash Chatbot", layout="centered")
st.title("⚡︎ Flash AI Personalized Chatbot")

# Session state
if "user_name" not in st.session_state:
    st.session_state.user_name, st.session_state.user_work = "", ""
if "chat_session" not in st.session_state:
    st.session_state.chat_session = []

# Step 6: User info input
if not st.session_state.user_name or not st.session_state.user_work:
    st.subheader("Tell me about yourself")
    name_in = st.text_input("Your name:")
    work_in = st.text_input("Your profession (e.g. Developer, Chef):")
    
    if st.button("Start Chat") and name_in and work_in:
        st.session_state.user_name = name_in.strip()
        st.session_state.user_work = work_in.strip()
        st.success(f"Welcome, {name_in} the {work_in}! Let's chat 😊")

        # Add header row to sheet if needed
        if sheet.row_count == 0 or not sheet.cell(1, 1).value:
            sheet.append_row(["Timestamp", "Name", "Profession", "Prompt"])

        st.rerun()

else:
    # Chat interaction
    user_q = st.chat_input("Ask me anything...")
    if user_q:
        st.session_state.chat_session.append(("user", user_q))

        # Save to Google Sheet
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([
            timestamp,
            st.session_state.user_name,
            st.session_state.user_work,
            user_q
        ])

        # Prompt LLM
        history_str = "\n".join([f"{r}: {c}" for r, c in st.session_state.chat_session[-6:]])
        inp = {
            "user_name": st.session_state.user_name,
            "user_work": st.session_state.user_work,
            "chat_history": history_str,
            "question": user_q
        }

        res = llm.invoke(prompt.format_messages(**inp))
        ai_resp = res.content
        st.session_state.chat_session.append(("assistant", ai_resp))

    # Display chat
    for role, msg in st.session_state.chat_session:
        st.chat_message(role).write(msg)

    if st.button("Clear Chat"):
        st.session_state.chat_session = []
        st.rerun()
