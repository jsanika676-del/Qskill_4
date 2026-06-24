import datetime
import json
import os
import sys
import io
import speech_recognition as sr
import pyttsx3
import requests
import sounddevice as sd
from scipy.io.wavfile import write

# Initialize the text-to-speech engine
engine = pyttsx3.init()

# Setup Voice (Optional: 0 for male, 1 for female)
voices = engine.getProperty('voices')
if voices:
    engine.setProperty('voice', voices[0].id) 

def speak(text):
    """Makes the assistant speak the given text."""
    print(f"Assistant: {text}")
    engine.say(text)
    engine.runAndWait()

def listen_command():
    """Listens for audio using sounddevice instead of PyAudio."""
    recognizer = sr.Recognizer()
    fs = 44100     # Sample rate (CD quality audio)
    seconds = 4    # Total length of time to listen per phrase

    print("\nListening...")
    try:
        # Record raw audio arrays straight from the hardware mic
        recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()  # Wait dynamically until the hardware mic finishes recording
        print("Recognizing...")

        # Convert the raw array into a virtual in-memory WAV file
        wav_io = io.BytesIO()
        write(wav_io, fs, recording)
        wav_io.seek(0)

        # Stream the virtual file directly into Google's processing API
        with sr.AudioFile(wav_io) as source:
            audio = recognizer.record(source)
            query = recognizer.recognize_google(audio, language='en-in')
            print(f"User said: {query}\n")
            return query.lower()

    except sr.UnknownValueError:
        speak("I didn't quite catch that. Could you repeat it?")
        return "none"
    except Exception as e:
        # Silently skip timeout drops or minor system hiccups
        return "none"

def get_weather(city):
    """Fetches real-time weather using wttr.in (No API key required)."""
    try:
        url = f"https://wttr.in/{city}?format=%C+and+%t"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            weather_report = response.text.strip().replace("+", " ")
            speak(f"The weather in {city} is currently {weather_report}.")
        else:
            speak("I couldn't retrieve the weather details right now.")
    except Exception:
        speak("I'm having trouble connecting to the weather service.")

def get_news():
    """Fetches top global headlines from an open API."""
    try:
        url = "https://saurav.tech/NewsAPI/top-headlines/category/general/in.json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])[:3]
            speak("Here are the top three news headlines:")
            for i, article in enumerate(articles, 1):
                speak(f"Headline {i}: {article['title']}")
        else:
            speak("I failed to fetch the latest news updates.")
    except Exception:
        speak("I am unable to reach the news server.")

# Main Assistant Loop
if __name__ == "__main__":
    speak("Hello! I am your personal assistant. How can I help you today?")
    
    while True:
        query = listen_command()
        
        if query == "none" or not query.strip():
            continue
            
        # 1. Check Time
        if "time" in query:
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            speak(f"The current time is {current_time}.")
            
        # 2. Check Weather
        elif "weather" in query:
            speak("Which city's weather would you like to check?")
            city = listen_command()
            if city != "none" and city.strip():
                get_weather(city)
            else:
                speak("I didn't hear a city name, canceling weather request.")
                
        # 3. Read News
        elif "news" in query:
            get_news()
            
        # 4. Set a Quick Reminder
        elif "reminder" in query or "remind me" in query:
            speak("What should I remind you about?")
            reminder_text = listen_command()
            if reminder_text != "none" and reminder_text.strip():
                speak(f"Got it. I will remind you to: {reminder_text}.")
                with open("reminders.txt", "a", encoding="utf-8") as f:
                    f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}: {reminder_text}\n")
            else:
                speak("I didn't catch the reminder details, canceling request.")
                    
        # 5. Exit the assistant
        elif "exit" in query or "stop" in query or "bye" in query:
            speak("Goodbye! Have a great day.")
            sys.exit()
            
        else:
            speak("I can help you check the weather, read the news, tell the time, or set a reminder. Please try again.")