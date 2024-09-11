from flask import Flask, render_template, request, jsonify
import os
import google.generativeai as genai
import speech_recognition as sr
import tempfile
import edge_tts
import asyncio

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
    audio_file_path = os.path.join(audio_path, 'output.mp3')
    
    communicate = edge_tts.Communicate(text, voice="id-ID-ArdiNeural")
    await communicate.save(audio_file_path)
    
    return audio_file_path  # Return the relative path to the file

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
