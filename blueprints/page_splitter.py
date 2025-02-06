from flask import Blueprint, render_template, request, redirect, send_file
from PIL import Image
from PyPDF2 import PdfReader
page_splitter = Blueprint('page_splitter', __name__)

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

@page_splitter.route('/remarkable_splitter')
def remarkable_splitter():
    return render_template('pdf.html')

@page_splitter.route('/upload', methods=['GET', 'POST'])
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