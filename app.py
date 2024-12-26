import os
from flask import Flask, render_template, request, redirect, url_for
import pdfplumber
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/explore', methods=['GET', 'POST'])
def explore():
    if request.method == 'POST':
        # Check if the file is in the request
        if 'file' not in request.files:
            return "No file uploaded", 400
        
        file = request.files['file']
        if file.filename == '':
            return "No selected file", 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Extract data from the PDF
            extracted_data, images = extract_pdf_data(file_path)

            return render_template('explore.html', data=extracted_data, images=images)
    
    return render_template('explore.html')

@app.route('/login')
def login():
    return render_template('login.html')


def extract_pdf_data(file_path):
    extracted_data = {}
    images = []

    with pdfplumber.open(file_path) as pdf:
        text = ""
        # Combine text from all pages for a more consistent extraction
        for page in pdf.pages:
            text += page.extract_text()

        # Print the full text for debugging
        print(text)

        # Extract data using refined regex
        extracted_data['name'] = find_field_value(text, 'Name')
        extracted_data['number'] = find_field_value(text, 'Phone')
        extracted_data['address'] = find_field_value(text, 'Address')

        # Extract images from pages
        for page in pdf.pages:
            for img in page.images:
                x0, top, x1, bottom = img['x0'], img['top'], img['x1'], img['bottom']
                cropped_image = page.within_bbox((x0, top, x1, bottom)).to_image()
                # Save the image in the static folder
                image_path = os.path.join('static', 'extracted.png')
                cropped_image.save(image_path)
                images.append('extracted.png')

    return extracted_data, images



def find_field_value(text, field_name):
    import re
    # Match the field_name followed by any amount of space or colon, then capture all characters until the next field
    pattern = rf"{field_name}[:\s]*([^\n]+)"  # Capture everything after the field name until a newline
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "Not found"



if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
