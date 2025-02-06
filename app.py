from flask import Flask, request, redirect, url_for, send_file, render_template, jsonify
import pandas as pd
import numpy as np
import os
from PIL import Image
from PyPDF2 import PdfReader
import json
from fuzzywuzzy import fuzz

app = Flask(__name__)
default_max_chip=[50,50,50,50,100]

@app.route("/poker", methods=[ 'POST', 'GET'])
def poker_chip_calculator():
    if request.method == 'POST':


        form_data = request.form

        print( form_data.get('buyin'))

        ChipValues=[form_data.get('black_value'),form_data.get('green_value'),form_data.get('blue_value'),form_data.get('red_value'),form_data.get('white_value')]
        ChipValues=[float(x) for x in ChipValues]

        min_chip_counts= [form_data.get('black_min'),form_data.get('green_min'),form_data.get('blue_min'),form_data.get('red_min'),form_data.get('white_min')]
        min_chip_counts=[int(x) for x in min_chip_counts]

        max_chip_counts=[form_data.get('black_max'),form_data.get('green_max'),form_data.get('blue_max'),form_data.get('red_max'),form_data.get('white_max')]
        max_chip_counts=[int(x) for x in max_chip_counts]

        buyIn=int(form_data.get('buyin'))
        num_players=int(form_data.get('num_players'))


        try:
            for x in range(5):
                if max_chip_counts[x] ==0:
                    max_chip_counts[x]=default_max_chip[x]/num_players
        except:
            print()

        PositiveIntSolToSpan_sorted = sort_2dlist(PositiveIntSolToSpan(ChipValues,buyIn,max_chip_counts,min_chip_counts))

        df = pd.DataFrame(PositiveIntSolToSpan_sorted, columns=['Black', 'Green', 'Blue', 'Red', 'White'])
        df= df.iloc[::-1, ::-1]
        df = df.sort_values(by='White',ascending=False)
        html_table = color_code_df(df)
        return render_template('pokerCountDisplay.html',  tables=[html_table], titles=df.columns.values)

    user_agent = request.headers.get('User-Agent')

    # Detect if the user is on mobile or desktop
    if "Mobile" in user_agent or "Android" in user_agent or "iPhone" in user_agent:
        return render_template('mobile.html')
    else:
        return render_template('pokerWeb.html')
    
    return render_template('mobile.html')



def color_code_df(df):
    # Start building the HTML table
    html = '<table border="1" style="border-collapse: collapse;">'

    # Add table headers
    html += '<tr>'
    for col in df.columns:
        html += f'<th>{col}</th>'
    html += '</tr>'

    # Add table rows
    for j in range(len(df)):
        html += '<tr>'
        for i in range(len(df.columns)):
            # Apply class based on the column index
            html += f'<td class="col-{i + 1}">{df.iloc[j, i]}</td>'
        html += '</tr>'

    html += '</table>'
    return html



def PositiveIntSolToSpan(ChipValues,buyIn,max_chip_counts,min_chip_counts):
    coefficients, total, max_chip_counts,min_chip_counts = ChipValues,buyIn,max_chip_counts,min_chip_counts
    var_ranges = [np.arange(0, int(total/coefficients[0])+1)]*len(coefficients)

    num_vars = len(coefficients)

    grids = np.meshgrid(*var_ranges[:-1])

    solution= []


    sum_terms = np.zeros_like(grids[0], dtype=float)
    for i in range(num_vars - 1):
        sum_terms += coefficients[i] * grids[i]

    last_var_range = var_ranges[-1]
    last_coefficient = coefficients[-1]
    last_var_grid = (total - sum_terms) / last_coefficient

    solution=[]

    grid_shape = grids[0].shape
    for index in np.ndindex(grid_shape):
        values = [int(grids[i][index]) for i in range(num_vars - 1)]
        last_var_value = last_var_grid[index]

        if last_var_value.is_integer() and last_var_value>=0:
            values = values + [int(last_var_value)]
            if checkChipCounts(values,max_chip_counts,min_chip_counts):
                solution.append(values)

    return solution


def checkChipCounts(counts,max_chip_counts,min_chip_counts):
  for x in range(len(counts)):
    if counts[x]>max_chip_counts[x] or counts[x]<min_chip_counts[x]:
      return False
  return True


def sort_2dlist(list_of_lists):
  return sorted(list_of_lists, key=lambda x: x)


# Create an uploads folder
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Ensure upload and output directories exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

def split_image_to_pdf(image_path, output_pdf_path, new_width=2550, chunk_height=3300):
    # Open the image
    img = Image.open(image_path)

    # Calculate the scaling factor for the width
    width_percent = (new_width / float(img.size[0]))
    new_height = int((float(img.size[1]) * float(width_percent)))

    # Resize the image to the new width while maintaining aspect ratio
    img = img.resize((new_width, new_height), Image.LANCZOS)

    # Calculate the number of chunks needed
    num_chunks = (new_height // chunk_height) + 1

    # Store the image chunks
    image_chunks = []

    # Split the image into chunks
    for i in range(num_chunks):
        # Calculate the bounding box for each chunk
        top = i * chunk_height
        bottom = top + chunk_height if (top + chunk_height) < new_height else new_height

        # Crop the image chunk
        img_chunk = img.crop((0, top, new_width, bottom))

        # Convert to RGB if the image has an alpha channel (transparency)
        if img_chunk.mode in ("RGBA", "LA"):
            img_chunk = img_chunk.convert("RGB")

        # Append the chunk to the list
        image_chunks.append(img_chunk)

    # Save the chunks as a single PDF
    image_chunks[0].save(output_pdf_path, save_all=True, append_images=image_chunks[1:])

@app.route('/remarkable_splitter')
def remarkable_splitter():
    return render_template('pdf.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)

        if file and file.filename.endswith(('.png', '.jpg', '.jpeg','.pdf')):
            file_path = "uploads/"+file.filename
            file.save(file_path)

            # Process the file accordingly
            if file.filename.endswith('.pdf'):
                # Extract the first page from the PDF and convert it to an image
                reader = PdfReader(file_path)
                page = reader.pages[0]

                # Save the page as an image (this might require additional processing)
                image_path = "uploads/" + file.filename + ".png"
                page_image = page.to_image()  # Requires pdf2image
                page_image.save(image_path)
            else:
                # Save the image file directly
                image_path = file_path

            # Process the image and split it into PDF

            output_pdf_path = "output/" + file.filename + "_split.pdf"
            split_image_to_pdf(image_path, output_pdf_path)

            # Return the PDF
            return send_file(output_pdf_path, as_attachment=True)
    return render_template('pdf.html')

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('home.html')


with open('taming_of_the_shrew.json', 'r') as f:
    script_data = json.load(f)

@app.route('/line_memorizer')
def line_memorizer():
    characters = sorted(set(line['speaker'] for act in script_data["acts"] for scene in act["scenes"] for line in scene["lines"]))
    return render_template('line_memorizer.html', characters=characters)

@app.route('/get_script', methods=['POST'])
def get_script():
    return jsonify(script_data)

@app.route('/toggle_lines', methods=['POST'])
def toggle_lines():
    selected_character = request.json.get('character')
    return jsonify({"character": selected_character})

@app.route('/check_speech', methods=['POST'])
def check_speech():
    data = request.get_json()
    spoken_text = data.get("spoken_text")
    correct_text = data.get("correct_text")

    print(f"Spoken: {spoken_text}")
    print(f"Correct: {correct_text}")

    if not spoken_text or not correct_text:
        return jsonify({"result": "Error: Missing data", "correct": False})

    # Simple case-insensitive comparison (can improve with NLP)
    ratio = fuzz.ratio(spoken_text.strip().lower(), correct_text.strip().lower())
    if ratio > 80:
        return jsonify({"result": "Correct!", "correct": True})
    return jsonify({"result": "Try again!", "correct": False})



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)