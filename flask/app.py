from flask import Flask, render_template, request, jsonify
import os
import google.generativeai as genai
import speech_recognition as sr
import tempfile
import edge_tts
import asyncio
import time
import noisereduce as nr
import numpy as np

# Flask app initialization
app = Flask(__name__)

# Configure Gemini API
os.environ["API_KEY"] = "AIzaSyAq9ro3j2APQL0VrPWhveWdteiCn9rbFFE"  # Gantilah dengan API key Anda
genai.configure(api_key=os.environ["API_KEY"])
model_name = "ogi"
model_role = "Asisten Virtual Berbasis AI untuk Menjawab Pertanyaan dalam Bahasa Indonesia"
model = genai.GenerativeModel('gemini-1.5-flash')

# Function for text-to-speech using Edge TTS
async def text_to_speech(text, lang='id'):
    audio_path = os.path.join('static', 'audio')
    if not os.path.exists(audio_path):
        os.makedirs(audio_path)  # Buat direktori jika belum ada

    # Beri nama unik untuk setiap file audio dengan menggunakan timestamp
    unique_filename = f"output_{int(time.time())}.mp3"
    audio_file_path = os.path.join(audio_path, unique_filename)
    
    communicate = edge_tts.Communicate(text, voice="id-ID-ArdiNeural")
    await communicate.save(audio_file_path)
    
    # Hapus file audio lama jika ada
    clear_old_audio_files(audio_path)
    
    return audio_file_path  # Return the relative path to the file

# Function to clear old audio files in the directory
def clear_old_audio_files(directory):
    files = os.listdir(directory)
    if len(files) > 1:
        for file in files[:-1]:  # Delete all except the latest file
            os.remove(os.path.join(directory, file))

# Function for speech-to-text using SpeechRecognition
def speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Silakan bicara...")
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio, language="id-ID")
        return text
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        return None

# Function for speech-to-text using SpeechRecognition with noise reduction
def speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        # Adjust for ambient noise to reduce background noise
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Silakan bicara...")
        audio = recognizer.listen(source)

    try:
        # Convert the audio to an array format for processing
        audio_data = np.frombuffer(audio.get_raw_data(), np.int16)

        # Apply noise reduction
        reduced_noise_audio = nr.reduce_noise(y=audio_data, sr=source.SAMPLE_RATE)

        # Convert back to AudioData format after noise reduction
        reduced_audio = sr.AudioData(reduced_noise_audio.tobytes(), source.SAMPLE_RATE, audio.sample_width)

        # Recognize the speech
        text = recognizer.recognize_google(reduced_audio, language="id-ID")
        return text

    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        return None

# Function to generate content using Gemini AI
def generate_content(prompt):
    full_prompt = f"{model_name}, {model_role}. {prompt}"
    response = model.generate_content(full_prompt)
    return response.text

# Flask route to render the HTML page
@app.route('/')
def index():
    return render_template('index.html')

# Flask route to handle speech-to-text-to-speech interaction
@app.route('/process', methods=['POST'])
def process():
    # Capture speech input using speech-to-text
    input_text = speech_to_text()
    
    if input_text:
        print(f"👨User: {input_text}")
        
        # Generate AI response using Gemini
        prompt = f"Berikan respons dengan singkat dan jelas, jangan gunakan emoticon: {input_text}"
        response = generate_content(prompt)
        print(f"🕵️Klaris: {response}")
        
        # Convert text to speech and save as audio file
        audio_file = asyncio.run(text_to_speech(response))
        
        # Return the user question, response, and audio file path
        return jsonify({'user_question': input_text, 'response': response, 'audio_file': audio_file})
    
    return jsonify({'error': 'Tidak dapat mendeteksi suara.'})

if __name__ == "__main__":
    app.run(debug=True)
