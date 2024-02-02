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
from hashlib import sha256
import time
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


def extract_summary(text):
    # Example: Extract summary based on a pattern or keyword
    match = re.search(r'Summary:([\s\S]*?)(?=\n\w+:)', text)
    return match.group(1).strip() if match else "Summary Not Found"

def extract_experience(text):
    # Example: Extract experience section
    match = re.search(r'Experience:([\s\S]*?)(?=\n\w+:)', text)
    return match.group(1).strip() if match else "Experience Not Found"

def extract_education(text):
    # Example: Extract education details
    match = re.search(r'Education:([\s\S]*?)(?=\n\w+:)', text)
    return match.group(1).strip() if match else "Education Not Found"

def extract_contact(text):
    # Example: Extract contact information
    # This is highly variable and might need a more complex approach
    match = re.search(r'Contact:([\s\S]*?)(?=\n\w+:)', text)
    return match.group(1).strip() if match else "Contact Info Not Found"

def extract_name(text):
    # Example: Extract the name using a pattern
    match = re.search(r'^[A-Z][a-z]*\s[A-Z][a-z]*', text)
    return match.group() if match else "Name Not Fytound"

extracted_text = "This is an example text with  extra   spaces   and special characters !@#$."
cleaned_text = preprocess_text(extracted_text)
print(cleaned_text)
    
def extract_resume_data(resume_file):
    extracted_text = extract_text_from_pdf(resume_file)
    preprocessed_text = preprocess_text(extracted_text)

    name = extract_name(preprocessed_text)
    summary = extract_summary(preprocessed_text)
    experience = extract_experience(preprocessed_text)
    education = extract_education(preprocessed_text)
    contact = extract_contact(preprocessed_text)

    return name, summary, experience, education, contact

# Example function to extract name - this will need specific logic based on your resume formats
def extract_name(text):
    # Implement logic to find and return the name, e.g., using regular expressions
    pass


# Similarly, implement extract_summary, extract_experience, extract_education, and extract_contact


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
        concatenated_summaries = ""
        for chunk in text_chunks:
            result = summarize_text_with_openai(chunk)
            if result["summary"]:
                final_summaries.append(f'<section><p>{result["summary"]}</p></div></section>')
            else:
                error_message = result["error"] or "No summary available for this section."
                final_summaries.append(f'<section><p>{error_message}</p></section>')

        return jsonify({"html_summaries": final_summaries or ["No summary available."]})

        action = request.form.get('action', 'summary')
        if action == 'summary':
                return jsonify({"html_summaries": final_summaries})
        else:
            # Generate website content
            website_details = parse_website_content(concatenated_summaries)
            background_image = fetch_pexels_image('1422286')
            return render_template('generated_website.html', **website_details, background_image=background_image)

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": str(e)}), 500



def fetch_pexels_video():
    # List of video IDs
    video_ids = ['853789', '853870', '853797', '7655497', '4629264', '7437509', '6193202', '7437144', '853878', '901234']
    
    # Select a random video ID from the list
    selected_video_id = random.choice(video_ids)

    api_key = 'ol6Ck5mBAkKtOOnWrTQ4CyyIquNlS54c9EOv0L0MhLp7wNoe0vaHVKw7'
    url = f'https://api.pexels.com/videos/videos/{selected_video_id}'
    headers = {'Authorization': api_key}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        video_data = response.json()
        video_url = video_data['video_files'][0]['link']  # Choose appropriate quality
        return video_url
    else:
        return 'https://i.vimeocdn.com/video/829185695-1700d0e1949013fd6b8b51b58ff8f59c7e6fbea01104a0e7eef746666a7c7fe9-d'  # Provide a default video URL in case of failure

def parse_website_content(content):
    structured_content = ""
    lines = content.split('\n')

    for line in lines:
        if line.endswith(':'):  # Simple check for headers
            structured_content += f"<h2>{line}</h2>"
        elif line.startswith('- '):  # Simple check for list items
            structured_content += f"<ul><li>{line[2:]}</li></ul>"
        else:
            structured_content += f"<p>{line}</p>"

    return structured_content



# Function to extract the first name
def extract_first_name(text):
    match = re.search(r"\b[A-Z][a-z]*\b", text)
    return match.group() if match else "Name Not Found"

def parse_links_and_emails(text):
    # Regular expression patterns for URLs and email addresses
    url_pattern = r'(https?://[^\s]+|www\.[^\s]+)'
    email_pattern = r'([a-zA-Z0-9+._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)'

    # Replace URLs with anchor tags, adding 'http://' prefix if missing
    text = re.sub(url_pattern, lambda x: '<a href="{}{}">{}</a>'.format('' if x.group().startswith('http') else 'http://', x.group(), x.group()), text)

    # Replace emails with mailto links
    text = re.sub(email_pattern, r'<a href="mailto:\1">\1</a>', text)

    return text


@app.route('/generate_website', methods=['POST'])
def generate_website():
    try:
        resume_file = request.files['resume_file']
        avatar_url = request.form.get('avatar_url') 
        extracted_text = extract_text_from_pdf(resume_file)
        preprocessed_text = preprocess_text(extracted_text)

        # Extract the first name for the header
        first_name = extract_first_name(preprocessed_text)

        # Modify your OpenAI prompt for English B2 professional tone
        prompt = f"Please create a website content in a professional English tone, B-2 level English, summarize the content to make it semantic and easy to read and digest from this resume:\n\n{preprocessed_text}"
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
        )

        ai_generated_content = response.choices[0].message.content.strip()
         # Process links and emails
        # Process links and emails
        processed_content = parse_links_and_emails(ai_generated_content)

# Render the webpage with processed content
        structured_content = parse_website_content(processed_content)
    
        # Generate AI-based header title
        nameCV = request.form.get('nameCV', '')
        header_prompt = f"Generate a dynamic header title starting with 'I am {nameCV}' based on the following resume content:\n\n{processed_content}"
    
        header_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative assistant."},
                {"role": "user", "content": header_prompt}
            ],
            max_tokens=50
)
        header_title = header_response.choices[0].message.content.strip()
    
        # Generate a unique slug
        slug = sha256(ai_generated_content.encode()).hexdigest()[:10] + str(int(time.time()))

        # Fetch the background video URL
        background_video = fetch_pexels_video()

        # Render the webpage with full structure
        
        full_html_content = render_template('generated_website.html', 
                                            header_title=header_title, 
                                            content=structured_content, 
                                            background_video=background_video,
                                            avatar_url=avatar_url) 

        # Save the generated content to a file
        filepath = f"my_tiny_website/{slug}.html"
        with open(filepath, "w") as file:
            file.write(full_html_content)

        # Construct the URL for the generated website (not using 'static')
        generated_url = f"{request.url_root}my_tiny_website/{slug}"

        # Return the URL in the response
        return jsonify({"url": generated_url})

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/my_tiny_website/<slug>')
def generated_website(slug):
    try:
        with open(f"my_tiny_website/{slug}.html", "r") as file:
            content = file.read()
        return content
    except IOError:
        return "Not Found", 404

    
    
if __name__ == '__main__':
    app.run(debug=True)