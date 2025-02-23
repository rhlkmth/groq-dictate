import streamlit as st
import sounddevice as sd
import wave
import tempfile
import os
import time
import base64
import pyperclip
from groq import Groq

# Streamlit UI setup
st.title("Voice Dictation App using Groq API")

# API Key Input
groq_api_key = st.text_input("Enter Groq API Key:", type="password")

if not groq_api_key:
    st.warning("Please enter your Groq API key to use this app.")
    st.stop()

# Initialize session state for recording and transcription
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'transcribed_text' not in st.session_state:
    st.session_state.transcribed_text = ""

# Recording parameters
fs = 16000  # Sample rate
channels = 1  # Mono audio

# Record button
if st.button(label="Record", type="primary", disabled=not groq_api_key):
    if not st.session_state.recording:
        st.session_state.recording = True
        st.session_state.transcribed_text = "Recording..."
        my_bar = st.progress(0)

        try:
            with wave.open(tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(2)  # 16-bit PCM
                wf.setframerate(fs)

                def callback(indata, frames, time_info, status):
                    wf.writeframes(indata.tobytes())
                    return None

                stream = sd.InputStream(samplerate=fs, channels=channels, dtype='int16', callback=callback)

                with stream:
                    seconds = 0
                    while st.session_state.recording:
                        time.sleep(1)
                        seconds += 1
                        progress_percent = min(seconds * 5, 100) # arbitrary progress for visual feedback
                        my_bar.progress(progress_percent)
                        if not st.session_state.recording: # check again inside loop for immediate stop
                            break

        except Exception as e:
            st.error(f"Error during recording: {e}")
            st.session_state.recording = False
            st.session_state.transcribed_text = "Recording Error."
            my_bar.empty()
            st.stop()

        my_bar.empty() # clear progress bar
        st.session_state.transcribed_text = "Processing audio..."

        # Transcription process after recording stops
        try:
            with st.spinner("Transcribing audio..."):
                audio_file_path = wf.name # get the name of the temporary file
                client = Groq(api_key=groq_api_key)

                with open(audio_file_path, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="distil-whisper-large-v3-en",
                        file=(os.path.basename(audio_file_path), audio_file, "audio/wav")
                    )
                st.session_state.transcribed_text = transcript.text

        except Exception as e:
            st.error(f"Error during transcription: {e}")
            st.session_state.transcribed_text = "Transcription Error."
        finally:
            os.unlink(audio_file_path) # clean up temp file

    else:
        st.session_state.recording = False
        st.session_state.transcribed_text = "Stopping recording, processing..."

# Stop Recording logic (using session state to control recording)
if st.session_state.recording:
    st.session_state.recording = False
    st.info("Click 'Record' again to start a new recording.")


# Text Area for Transcribed Text
transcribed_text_area = st.text_area("Transcribed Text:", value=st.session_state.transcribed_text, height=200)

# Copy to Clipboard Button
if st.session_state.transcribed_text and st.session_state.transcribed_text != "Recording..." and st.session_state.transcribed_text != "Processing audio..." and st.session_state.transcribed_text != "Transcription Error." and st.session_state.transcribed_text != "Recording Error." :
    if st.button("Copy to Clipboard"):
        pyperclip.copy(st.session_state.transcribed_text)
        st.success("Text copied to clipboard!")
