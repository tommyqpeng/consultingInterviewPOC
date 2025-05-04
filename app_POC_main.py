# -*- coding: utf-8 -*-
"""
Created on Sun May  4 18:20:24 2025

@author: tommy
"""

import streamlit as st
import requests
import json

# --- Load secrets from Streamlit Cloud or local secrets.toml ---
DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
APP_PASSWORD = st.secrets["APP_PASSWORD"]

# --- Password Gate ---
st.title("Interview Coaching GPT (Powered by DeepSeek)")
password = st.text_input("Enter access password", type="password")
if password != APP_PASSWORD:
    st.warning("Please enter the correct password to continue.")
    st.stop()

# --- Interview Prompt ---
question = "Our client, a cement company CementX from Australia would like to enter the Chinese market. What are some key considerations?"

# --- Scoring Rubric ---
RUBRIC = """
Score this case interview answer (0–10) using the following criteria:
1. Problem structuring and logic
2. Business judgment
3. Communication clarity
4. Insightfulness

Provide a numeric score and 2–3 sentences of feedback.
"""

# --- UI ---
st.markdown(f"###Interview Question:\n**{question}**")
user_input = st.text_area("Paste your answer here:", height=200)

if st.button("Get Feedback") and user_input.strip():
    with st.spinner("Analyzing your response with DeepSeek..."):

        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "deepseek-chat",  # change if you're using a different model like deepseek-coder
            "messages": [
                {"role": "system", "content": "You are a McKinsey case interview coach scoring responses."},
                {"role": "user", "content": f"{RUBRIC}\n\nInterview question: {question}\nCandidate's answer:\n{user_input}"}
            ],
            "temperature": 0.4
        }

        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload)
        )

        if response.status_code == 200:
            result = response.json()
            feedback = result["choices"][0]["message"]["content"]
            st.success("Done!")
            st.markdown("### 🔍 Feedback:")
            st.write(feedback)
        else:
            st.error(f"❌ API Error: {response.status_code}")
            st.code(response.text)
