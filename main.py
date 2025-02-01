import tkinter as tk
from tkinter import scrolledtext
import speech_recognition as sr
import requests
from gtts import gTTS
import os
import playsound
import threading

# Hugging Face API settings 
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/deepseek-ai/DeepSeek-R1"

# Function to recognize speech
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        update_chat("Listening...", "bot")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        update_chat(text, "user")
        process_text(text)
    except sr.UnknownValueError:
        update_chat("Could not understand audio.", "bot")
    except sr.RequestError:
        update_chat("Error with speech recognition service.", "bot")

# Function to query LLM (Hugging Face)
def query_llm(text):
    payload = {"inputs": text}
    response = requests.post(HUGGINGFACE_API_URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        return response.json()[0]["generated_text"]
    else:
        return "I couldn't process that."

# Function to convert text to speech
def text_to_speech(text):
    tts = gTTS(text=text, lang="en")
    tts.save("response.mp3")
    playsound.playsound("response.mp3")
    os.remove("response.mp3")

# Function to process text (from input field or speech)
def process_text(text):
    response_text = query_llm(text)
    update_chat(response_text, "bot")
    threading.Thread(target=text_to_speech, args=(response_text,)).start()

# Function to update the chatbox
def update_chat(text, sender):
    if sender == "user":
        chatbox.insert(tk.END, f"You: {text}\n", "user")
    else:
        chatbox.insert(tk.END, f"Bot: {text}\n", "bot")
    chatbox.yview(tk.END)

# Function to send text input from the user
def send_text():
    text = entry.get()
    if text:
        update_chat(text, "user")
        entry.delete(0, tk.END)
        process_text(text)

# Creating the GUI
root = tk.Tk()
root.title("Speech-to-Chatbot")

# Chatbox
chatbox = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=20)
chatbox.pack(padx=10, pady=10)
chatbox.tag_config("user", foreground="blue")
chatbox.tag_config("bot", foreground="green")

# Entry field
entry = tk.Entry(root, width=40)
entry.pack(side=tk.LEFT, padx=10, pady=5)

# Send button
send_button = tk.Button(root, text="Send", command=send_text)
send_button.pack(side=tk.LEFT, padx=5)

# Speech recognition button
mic_button = tk.Button(root, text="🎤 Speak", command=lambda: threading.Thread(target=recognize_speech).start())
mic_button.pack(side=tk.LEFT, padx=5)

root.mainloop()
