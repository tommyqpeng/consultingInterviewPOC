import streamlit as st
import gspread
import json
import re
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from util_functions import decrypt_file, transcribe_audio, build_prompt, generate_feedback
from st_audiorec import st_audiorec

# --- Config and Secrets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GSHEET_CREDS"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(st.secrets["AnswerStorage_Sheet_ID"]).sheet1

APP_PASSWORD = st.secrets["APP_PASSWORD"]
DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
DECRYPTION_KEY = st.secrets["DECRYPTION_KEY"].encode()
DEEPGRAM_API_KEY = st.secrets["DEEPGRAM_API_KEY"]

# --- Session State ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "password_attempts" not in st.session_state:
    st.session_state.password_attempts = 0
if "audio_submitted" not in st.session_state:
    st.session_state.audio_submitted = False
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None
if "submitted" not in st.session_state:
    st.session_state.submitted = False

st.title("Interview Answer Submission")

# --- Password Authentication ---
if not st.session_state.authenticated:
    password = st.text_input("Enter access password", type="password")
    if st.button("Submit Password"):
        if password == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.session_state.password_attempts += 1
            st.warning("Incorrect password.")
            st.stop()

# --- Main App (Post-authenticated) ---
if st.session_state.authenticated and not st.session_state.submitted:

    # --- Info ---
    st.markdown("""
    ### How It Works

    Once you submit your interview answer, it will be logged along with your name and email.  
    You will **receive feedback via email within 1 week** from an experienced **McKinsey interview coach**.

    Make sure your email is correct so we can get back to you.
    """)

    # --- User Info ---
    user_name = st.text_input("Your name")
    user_email = st.text_input("Your email address")
    email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"

    if not user_name or not user_email:
        st.info("Please enter your name and email to continue.")
        st.stop()
    if not re.match(email_pattern, user_email):
        st.warning("Please enter a valid email address.")
        st.stop()

    # --- Load Prompt Content ---
    prompt_data = decrypt_file("prompts.json.encrypted", DECRYPTION_KEY)
    question = prompt_data["question"]
    rubric = prompt_data["rubric"]
    system_role = prompt_data["system_role"]
    generation_instructions = prompt_data["generation_instructions"]

    # --- Input Method ---
    st.markdown("### Interview Question")
    st.markdown(question)
    input_method = st.radio("Choose input method:", ["Text", "Voice"])

    user_input = ""

    if input_method == "Text":
        user_input = st.text_area("Write your answer here:", height=200)

    else:  # Voice input
        if not st.session_state.audio_submitted:
            st.markdown("#### Record or upload your audio")
            uploaded_file = st.file_uploader("Upload .wav or .m4a file", type=["wav", "m4a"])
            audio_bytes = st_audiorec() or (uploaded_file.read() if uploaded_file else None)

            if audio_bytes:
                st.session_state.audio_submitted = True
                st.session_state.audio_bytes = audio_bytes
                st.rerun()
        else:
            with st.spinner("Transcribing..."):
                try:
                    user_input = transcribe_audio(st.session_state.audio_bytes, DEEPGRAM_API_KEY)
                    st.session_state.audio_submitted = False  # reset for next time
                    st.text_area("Transcript (edit if needed)", value=user_input, height=200, key="transcript_edit")
                except Exception as e:
                    st.session_state.audio_submitted = False
                    st.error(f"Transcription failed: {e}")
                    st.stop()

    # --- Submit ---
    if st.button("Submit Response") and user_input.strip():
        with st.spinner("Processing response and logging..."):
            try:
                prompt = build_prompt(question, rubric, [], user_input, generation_instructions)
                feedback = generate_feedback(prompt, system_role, DEEPSEEK_API_KEY)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                sheet.append_row([timestamp, user_name, user_email, user_input.strip(), feedback.strip()])
                st.session_state.submitted = True
                st.success("Submission complete! Your answer and feedback have been logged.")
            except Exception as e:
                st.session_state.submitted = True
                st.error(f"Something went wrong: {e}")

# --- Final Screen ---
if st.session_state.submitted:
    st.markdown("✅ Thank you! Your submission has been processed.")
