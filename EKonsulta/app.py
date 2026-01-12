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
        {"name": "EKAS EPRESS MCA", "url": "/static/pdfs/EKAS,EPRESS,MCA_OUTPUT.pdf"},
        {"name": "PKRF CONSENT HEALTH SCREENING", "url": "/static/pdfs/PKRF,Consent, Health Screening_OUTPUT.pdf"},
    ]
    return render_template("index.html", pdf_files=pdf_files)

@app.route("/submit_form", methods=["POST"])
def submit_form():
    data = request.get_json()
    pretty_json_string = json.dumps(data, indent=4)
    patient_data = dict(data)
    print(pretty_json_string)
    fill_EKAS_EPRESS_MCA(patient_data)
    fill_PKRF_CHS(patient_data)

    return jsonify({"status": "success", "message": "Form received"})

def fill_EKAS_EPRESS_MCA(data):
    try:
        pdf_path = os.path.join(current_app.root_path,"EKAS,EPRESS,MCA.pdf")
        output_pdf = os.path.join(current_app.root_path, "static", "pdfs", "EKAS,EPRESS,MCA_OUTPUT.pdf")
        form_fields_EKAS_EPRESS_MCA = list(fillpdfs.get_form_fields(pdf_path).keys())
        
        date_object = datetime.strptime(data["otherDetails"]["dob"], "%Y-%m-%d")
        formatted_date = date_object.strftime('%m-%d-%Y')

        age = today.year - date_object.year - (
            (today.month, today.day) < (date_object.month, date_object.day)
        )

        cellphoneNum = data["otherDetails"]["mobile"]
        patientMiddleName = (
            data["personalInfo"]["middleName"][0]
            if data["personalInfo"]["middleName"]
            else ""
        )
        patientFullName = f"{data['personalInfo']['firstName']} {patientMiddleName} {data['personalInfo']['lastName']} {data['personalInfo']['nameExt']}"

        member = "Yes" if data["patientIsMember"] == "member" else ""
        dependent = "Yes" if data["patientIsMember"] == "dependent" else ""

        data_EKAS_EPRESS_MCA = {
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("PatientName")]: patientFullName,
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("DOB")]: formatted_date,
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("PIN")]: data.get('pin',''),
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("BenefitYear")]: today.year,
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("FullnameAndDateBeneficiary")]: f"{patientFullName}\t\t {today.month:02}/{today.day:02}/{today.year}",
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("Member")]: member,
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("Dependent")]: dependent,
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("ContactNum")]: cellphoneNum,
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("Age")]: age,
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("Performed")]: "Yes",
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("DatePerformed")]: "TODAY"
        }

        fillpdfs.write_fillable_pdf(pdf_path, output_pdf, data_EKAS_EPRESS_MCA)
    except Exception as e: 
        print(f"This is the error {e}")

def fill_PKRF_CHS(data):
    try:
        pdf_path = os.path.join(current_app.root_path,"PKRF,Consent, Health Screening.pdf")
        output_pdf = os.path.join(current_app.root_path, "static", "pdfs", "PKRF,Consent, Health Screening_OUTPUT.pdf")
        form_fields_PKRF_Consent = list(fillpdfs.get_form_fields(pdf_path).keys())
        
        date_object = datetime.strptime(data["otherDetails"]["dob"], "%Y-%m-%d")
        formatted_date = date_object.strftime('%m-%d-%Y')

        age = today.year - date_object.year - (
            (today.month, today.day) < (date_object.month, date_object.day)
        )

        gender = data["otherDetails"]['sex']
        patientMiddleName = (
            data["personalInfo"]["middleName"][0]
            if data["personalInfo"]["middleName"]
            else ""
        )
        patientFullName = f"{data['personalInfo']['firstName']} {patientMiddleName} {data['personalInfo']['lastName']} {data['personalInfo']['nameExt']}"

        member = "Yes" if data["patientIsMember"] == "member" else ""
        dependent = "Yes" if data["patientIsMember"] == "dependent" else ""

        data_PKRF_CHS = {
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("Member")]: member,
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("Dependent")]: dependent,
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("PIN")]: data.get('pin',''),
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("DateToday")]: f"{today.month:02}/{today.day:02}/{today.year}",
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("LastName")]: data["personalInfo"]["lastName"],
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("FirstName")]: data["personalInfo"]["firstName"],
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("MiddleName")]: data["personalInfo"]["middleName"],
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("Barangay")]: data["address"]["barangay"],
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("Municipality")]: data["address"]["municipality"],
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("Province")]: "LEYTE",
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("DOB")]: formatted_date,
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("ContactNum")]: data["otherDetails"]["mobile"],
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("DepLastName")]: data["personalInfo"]["lastName"],
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("DepFirstName")]: data["personalInfo"]["firstName"],
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("DepMiddleName")]: data["personalInfo"]["middleName"],
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("PatientSignature")]: patientFullName,
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("PatientFullName")]: patientFullName,
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("FullAddress")]: f"{data['address']['barangay']}, {data['address']['municipality']}, LEYTE",
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("MemberPIN")]: data.get('pin',''),
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("DependentPIN")]: data.get('dependentPin',''),
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("NameExt")]: data["personalInfo"]["nameExt"],
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("Age")]: age,
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("Gender")]: gender,
        }

        fillpdfs.write_fillable_pdf(pdf_path, output_pdf, data_PKRF_CHS)
    except Exception as e:
        print(f"This is the error{e}")

def clean_files(file_list):
    for f in file_list:
        try:
            if os.path.exists(os.path.join(current_app.root_path, "static", "pdfs", f)):
                os.remove(os.path.join(current_app.root_path, "static", "pdfs", f))
                print(f"Deleted {f}")
        except Exception as e:
            print(f"Error deleting {f}: {e}")

@app.route("/get_pdfs")
def get_pdfs():
    clean_files(["output_cf1.pdf", "output_cf2.pdf","output_csf.pdf", "output_soa.pdf"])
    return jsonify([
        {
            "name": "EKAS EPRESS MCA",
            "url": url_for("static", filename="pdfs/EKAS,EPRESS,MCA_OUTPUT.pdf")
        },
        {
            "name": "PKRF CONSENT HEALTH SCREENING", 
            "url": url_for("static", filename="pdfs/PKRF,Consent, Health Screening_OUTPUT.pdf")
        },
    ])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)