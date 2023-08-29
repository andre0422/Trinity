from flask import Flask, render_template, request, redirect, url_for
from pdf2image import convert_from_bytes
from PIL import Image
import pytesseract
import spacy
import uuid
import os

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

app = Flask(__name__)

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'

    # Generate a unique filename
    file_name = str(uuid.uuid4())

    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()

    image_paths = []

    if file_ext == '.pdf':
        # Use pdf2image to convert PDF pages to images
        images = convert_from_bytes(file.read())
        
        for index, image in enumerate(images):
            path = os.path.join('static', f'{file_name}_{index}.png')
            image.save(path)
            image_paths.append(path)

        extracted_text = ''.join([pytesseract.image_to_string(image) for image in images])

    else:
        image = Image.open(file)
        image_path = os.path.join('static', f'{file_name}.png')
        image.save(image_path)
        image_paths = [image_path]
        extracted_text = pytesseract.image_to_string(image)

    # Split the extracted text by newline characters
    lines = [line.strip() for line in extracted_text.split('\n') if line.strip() != '']

    # Process the extracted text with spaCy for NER


    named_entities = []
    for line in lines:
        doc = nlp(line)
        for entity in doc.ents:
            if entity.label_ in ['DATE', 'MONEY', 'ORG', 'GPE', 'LOC', 'PERSON']:
                named_entities.append((entity.text, entity.label_))

    return render_template('results.html', ocr_text="\n".join(lines), entities=named_entities, images=image_paths)

if __name__ == '__main__':
    app.run(debug=True)
