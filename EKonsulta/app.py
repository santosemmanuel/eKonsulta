from flask import Flask, render_template, request, jsonify, current_app, url_for
from fillpdf import fillpdfs
from pdfrw import PdfReader as PdfRwReader, PdfWriter as PdfRwWriter, PageMerge, PdfDict, PdfName
from datetime import datetime, date
import os
import json

app = Flask(__name__)

today = date.today()

@app.route("/")
def index():
    pdf_files = [
        {"name": "EKAS EPRESS MCA", "url": "/static/pdfs/EKAS,EPRESS,MCA.pdf"},
        {"name": "PKRF CONSENT HEALTH SCREENING", "url": "/static/pdfs/output_cf2.pdf"},
    ]
    return render_template("index.html", pdf_files=pdf_files)

@app.route("/submit_form", methods=["POST"])
def submit_form():
    data = request.get_json()
    fill_EKAS_EPRESS_MCA(data)
    # fill_PKRF_CHS()

    return jsonify({"status": "success", "message": "Form received"})

def fill_EKAS_EPRESS_MCA(data):
    pdf_path = os.path.join(current_app.root_path,"EKAS,EPRESS,MCA.pdf")
    form_fields_EKAS_EPRESS_MCA = list(fillpdfs.get_form_fields(pdf_path).keys())
    print(form_fields_EKAS_EPRESS_MCA)

def fill_PKRF_CHS(data):
    pass

@app.route("/get_pdfs")
def get_pdfs():
    return jsonify([
        {
            "name": "PhilHealth Form",
            "url": url_for("static", filename="pdfs/philhealth.pdf")
        }
    ])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)