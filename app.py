# Step 1: Install dependencies
# pip install streamlit langchain langchain-google-genai python-dotenv

import streamlit as st
from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Step 2: Load Gemini API key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Step 3: Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.7,
    google_api_key=api_key
)

# Step 4: Prompt template with personalization and history injection
prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are a helpful, conversational assistant. The user is named {user_name} and works as a {user_work}. "
     "When replying, use their name naturally in the flow of conversation — not always at the start. "
     "Use analogies or examples from their profession ({user_work}) *only if* they help make your answer clearer. "
     "Be informative, concise, and human-like.\n"
     "Here's the recent conversation:\n{chat_history}"),
    
    ("human", "{question}")
])

# Step 5: Streamlit setup & session state
st.set_page_config(page_title="⚡︎ Flash Chatbot", layout="centered")
st.title("⚡︎ Flash AI Personlized Chatbot")

if "user_name" not in st.session_state:
    st.session_state.user_name, st.session_state.user_work = "", ""
if "chat_session" not in st.session_state:
    st.session_state.chat_session = []  # store (role, content) tuples

# Step 6: Ask for name/profession once
if not st.session_state.user_name or not st.session_state.user_work:
    st.subheader("Tell me about yourself")
    name_in = st.text_input("Your name:")
    work_in = st.text_input("Your profession (e.g. Developer, Chef):")
    if st.button("Start Chat") and name_in and work_in:
        st.session_state.user_name = name_in
        st.session_state.user_work = work_in
        st.success(f"Welcome, {name_in} the {work_in}! Let's chat 😊")
        st.rerun()
else:
    # Chat input
    user_q = st.chat_input("Ask me anything...")
    if user_q:
        st.session_state.chat_session.append(("user", user_q))

        # Build chat history string from last 3 messages
        history_str = "\n".join(
            [f"{r}: {c}" for r, c in st.session_state.chat_session[-6:]]
        )

        # Format prompt with variables & history
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
