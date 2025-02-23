import streamlit as st
import tempfile
import os
from groq import Groq
import pyperclip  # Import here, so it's available in the global scope

# Streamlit UI setup
st.title("Voice Dictation App using Groq API")

# API Key Input
groq_api_key = st.text_input("Enter Groq API Key:", type="password")

if not groq_api_key:
    st.warning("Please enter your Groq API key to use this app.")
    st.stop()

# Initialize session state for transcribed text
if 'transcribed_text' not in st.session_state:
    st.session_state.transcribed_text = ""

# File Uploader Widget
uploaded_file = st.file_uploader("Upload an audio file", type=["wav", "mp3", "m4a", "flac", "ogg", "webm", "mpga"])  # Supported formats

if uploaded_file is not None:
    st.session_state.transcribed_text = "Processing audio..."  # Show processing message

    # Save the uploaded file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        audio_file_path = tmp_file.name

    # Transcription process
    try:
        with st.spinner("Transcribing audio..."):
            client = Groq(api_key=groq_api_key)
            with open(audio_file_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="distil-whisper-large-v3-en",
                    file=(os.path.basename(audio_file_path), audio_file)  # No explicit content type needed
                )
            st.session_state.transcribed_text = transcript.text

    except Exception as e:
        st.error(f"Error during transcription: {e}")
        st.session_state.transcribed_text = "Transcription Error."
    finally:
        os.unlink(audio_file_path)  # Clean up the temporary file

# Display the transcribed text (handles initial state and updates)
transcribed_text_area = st.text_area("Transcribed Text:", value=st.session_state.transcribed_text, height=200)

# Copy to Clipboard Button (only show if there's transcribed text)
if st.session_state.transcribed_text and st.session_state.transcribed_text not in ("Processing audio...", "Transcription Error."):
    if st.button("Copy to Clipboard"):
        pyperclip.copy(st.session_state.transcribed_text)
        st.success("Text copied to clipboard!")

elif uploaded_file is None:
    st.info("Please upload an audio file (.wav, .mp3, .m4a, .flac, .ogg, .webm, .mpga).")
