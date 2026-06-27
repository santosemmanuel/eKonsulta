import cv2
import numpy as np
from pdf2image import convert_from_path
import img2pdf
import os

def change_scanned_pdf_color(input_pdf, output_pdf):
    # 1. Convert PDF pages to images
    print("Converting PDF to images...")
    poppler_path = r'C:\poppler-25.12.0\Library\bin' 
    images = convert_from_path(input_pdf, poppler_path=poppler_path)
    processed_images = []

    for i, image in enumerate(images):
        print(f"Processing page {i+1}...")
        # Convert PIL image to OpenCV format (BGR)
        open_cv_image = np.array(image)
        open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)

        # 2. Define color replacement (Replace Black with Red)
        # We use a threshold to handle slight grayness in scans
        lower_black = np.array([0, 0, 0], dtype="uint8")
        upper_black = np.array([100, 100, 100], dtype="uint8") # Adjust threshold if needed
        
        # Create a mask to identify black/dark gray pixels
        mask = cv2.inRange(open_cv_image, lower_black, upper_black)
        
        # Change masked pixels to Red (BGR: 0, 0, 255)
        open_cv_image[mask > 0] = [139, 0, 0]

        # 3. Save processed image temporary
        temp_filename = f"temp_page_{i}.png"
        cv2.imwrite(temp_filename, open_cv_image)
        processed_images.append(temp_filename)

    # 4. Convert images back to PDF
    print("Saving new PDF...")
    with open(output_pdf, "wb") as f:
        f.write(img2pdf.convert(processed_images))

    # 5. Clean up temporary images
    for temp_file in processed_images:
        os.remove(temp_file)
    print("Done!")

# Example usage
change_scanned_pdf_color("EMPANELMENT_(MCA)_user_2.pdf", "output_red.pdf")
