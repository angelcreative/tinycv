from flask import Flask, jsonify, request, render_template, Response, redirect, url_for, session, flash
from flask_cors import CORS
import hmac
import hashlib
import requests
import bcrypt
import os
import uuid
import random
import logging
import json
import PyPDF2
import re
from io import BytesIO
from dotenv import load_dotenv
load_dotenv()  # This loads the environment variables from the .env file
from openai import OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)



app = Flask(__name__)
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max file size: 16 MB



def extract_text_from_pdf(file):
    with BytesIO() as temp_buffer:
        temp_buffer.write(file.read())
        reader = PyPDF2.PdfReader(temp_buffer)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            text += page_text + "\n"
        return text
    
def preprocess_text(text):
    # Remove extra whitespace
    text = ' '.join(text.split())

    # Remove special characters and non-alphanumeric characters
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)

    return text

extracted_text = "This is an example text with  extra   spaces   and special characters !@#$."
cleaned_text = preprocess_text(extracted_text)
print(cleaned_text)
    


def summarize_text_with_openai(text):
    try:
        prompt = f"Create a brief summary in the first person for a resume with the following structure, within 230 characters: 'Hello 👋🏼 I'm a [summary section] [latest 3 jobs] [3 top skills] [languages if any] #tinycv #resume #opentowork'. Resume details:\n\n{text}"
        response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant that creates brief first-person resume summaries within 240 characters."},
        {"role": "user", "content": prompt}
    ],
    max_tokens=240,
)

        print("API Response:", response)  # Log the full response
        summary = response.choices[0].message.content.strip()
        return {"summary": summary, "error": None}
    except Exception as e:
        print("Error in API call:", str(e))  # Log the error
        return {"summary": None, "error": str(e)}





@app.route('/')
def index():
    return render_template('index.html')

def split_text(text, max_length):
    """
    Splits text into chunks where each chunk has a length less than or equal to max_length.
    """
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        if current_length + len(word) > max_length:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + 1  # Add 1 for space

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks
@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        extracted_text = extract_text_from_pdf(file)
        preprocessed_text = preprocess_text(extracted_text)
        max_length = 1000
        text_chunks = split_text(preprocessed_text, max_length)

        final_summaries = []
        for chunk in text_chunks:
            result = summarize_text_with_openai(chunk)
            if result["summary"]:
                final_summaries.append(f'<section><p>{result["summary"]}</p></div></section>')
            else:
                error_message = result["error"] or "No summary available for this section."
                final_summaries.append(f'<section><p>{error_message}</p></section>')

        return jsonify({"html_summaries": final_summaries or ["No summary available."]})

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)