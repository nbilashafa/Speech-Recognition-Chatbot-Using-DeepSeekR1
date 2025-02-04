import streamlit as st
import speech_recognition as sr
import requests
from gtts import gTTS
import os
import pygame
import threading
from PIL import Image
import io

# Ensure dependencies are available
try:
    import streamlit as st
    import speech_recognition as sr
    import requests
    from gtts import gTTS
    import pygame
    from PIL import Image
except ModuleNotFoundError as e:
    st.error(f"Missing dependency: {e.name}. Please install it before running the application.")

# Initialize pygame mixer
pygame.init()
pygame.mixer.init()

# Hugging Face API for DeepSeek-R1 (Set your API key)
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/deepseek-ai/deepseek-r1"
HEADERS = {"Authorization": "Bearer YOUR_HF_API_KEY"}  # Replace with your API key

# Function to recognize speech
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        st.session_state['messages'].append(("You", text))
        process_text(text)
    except sr.UnknownValueError:
        st.session_state['messages'].append(("Bot", "Could not understand audio."))
    except sr.RequestError:
        st.session_state['messages'].append(("Bot", "Error with speech recognition service."))

# Function to query LLM (DeepSeek-R1)
def query_llm(text):
    payload = {"inputs": text}
    try:
        response = requests.post(HUGGINGFACE_API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        return response.json().get("generated_text", "I couldn't process that.")
    except requests.exceptions.RequestException as e:
        return f"Error querying model: {str(e)}"

# Function to convert text to speech using pygame
def text_to_speech(text):
    tts = gTTS(text=text, lang="en")
    filename = "response.mp3"
    tts.save(filename)
    
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        continue  # Wait for the speech to finish playing
    
    os.remove(filename)

# Function to process text
def process_text(text):
    response_text = query_llm(text)
    st.session_state['messages'].append(("Bot", response_text))
    threading.Thread(target=text_to_speech, args=(response_text,)).start()

# Function to process image
def process_image(image):
    st.session_state['messages'].append(("Bot", "Analyzing image..."))
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="JPEG")
    image_bytes = image_bytes.getvalue()
    
    payload = {"inputs": image_bytes}
    try:
        response = requests.post(HUGGINGFACE_API_URL, headers=HEADERS, files={"image": image_bytes})
        response.raise_for_status()
        result = response.json().get("generated_text", "Couldn't analyze the image.")
        st.session_state['messages'].append(("Bot", result))
    except requests.exceptions.RequestException as e:
        st.session_state['messages'].append(("Bot", f"Error analyzing image: {str(e)}"))

# Streamlit UI
st.title("AI Chatbot with Speech & Image Support")

if 'messages' not in st.session_state:
    st.session_state['messages'] = []

for sender, message in st.session_state['messages']:
    st.write(f"**{sender}:** {message}")

user_input = st.text_input("Type your message:")
if st.button("Send"):
    if user_input:
        st.session_state['messages'].append(("You", user_input))
        process_text(user_input)

if st.button("🎤 Speak"):
    recognize_speech()

uploaded_image = st.file_uploader("", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
st.markdown("<label for='file_uploader' style='display:flex;align-items:center;gap:10px;'><span style='font-size:20px;'>📷 Upload an Image</span></label>", unsafe_allow_html=True)
if uploaded_image:
    image = Image.open(uploaded_image)
    st.image(image, caption="Uploaded Image", use_column_width=True)
    process_image(image)
