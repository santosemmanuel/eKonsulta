from flask import Flask, render_template, request, jsonify, current_app, url_for
from fillpdf import fillpdfs
from pdfrw import PdfReader as PdfRwReader, PdfWriter as PdfRwWriter, PageMerge, PdfDict, PdfName
from datetime import datetime, date
import os
import json
import mysql.connector
from dotenv import load_dotenv
from db import get_db_connection

app = Flask(__name__)
load_dotenv()
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

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 🔍 CHECK IF dependent_pin EXISTS
        cursor.execute(
            "SELECT id FROM patients WHERE dependent_pin = %s or pin = %s",
            (patient_data["dependentPin"],patient_data["pin"])
        )

        existing_patient = cursor.fetchone()

        if not existing_patient:
            # 🆕 INSERT NEW RECORD
            insert_query = """
                INSERT INTO patients (patient_is_member, pin, dependent_pin, created_at)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(
                insert_query,
                (
                    patient_data["patientIsMember"],
                    patient_data["pin"],
                    patient_data["dependentPin"],
                    datetime.now()
                )
            )

            patient_id = cursor.lastrowid

            # 🧍 INSERT personal_info
            cursor.execute("""
                INSERT INTO personal_info
                (patient_id, last_name, first_name, middle_name, name_ext,
                date_of_birth, sex, mobile)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                patient_id,
                patient_data["personalInfo"]["lastName"],
                patient_data["personalInfo"]["firstName"],
                patient_data["personalInfo"]["middleName"],
                patient_data["personalInfo"]["nameExt"],
                patient_data["otherDetails"]["dob"],
                patient_data["otherDetails"]["sex"],
                patient_data["otherDetails"]["mobile"]
            ))

            # 🏠 INSERT address
            cursor.execute("""
                INSERT INTO addresses
                (patient_id, municipality, barangay)
                VALUES (%s, %s, %s)
            """, (
                patient_id,
                patient_data["address"]["municipality"],
                patient_data["address"]["barangay"]
            ))


            conn.commit()


    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"status": "error", "message": "Database query failed"}), 500
    finally:
        cursor.close()
        conn.close()


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
        barangay = data["address"]["barangay"]

        data_PKRF_CHS = {
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("Member")]: member,
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("Dependent")]: dependent,
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("PIN")]: data.get('pin',''),
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("DateToday")]: f"{today.month:02}/{today.day:02}/{today.year}",
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("LastName")]: data["personalInfo"]["lastName"],
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("FirstName")]: data["personalInfo"]["firstName"],
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("MiddleName")]: data["personalInfo"]["middleName"],
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("Barangay")]: barangay.upper(),
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("Municipality")]: data["address"]["municipality"],
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("Province")]: "LEYTE",
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("DOB")]: formatted_date,
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("ContactNum")]: data["otherDetails"]["mobile"],
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("DepLastName")]: data["personalInfo"]["lastName"],
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("DepFirstName")]: data["personalInfo"]["firstName"],
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("DepMiddleName")]: data["personalInfo"]["middleName"],
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("PatientSignature")]: patientFullName,
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("PatientFullName")]: patientFullName,
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("FullAddress")]: f"{barangay.upper()}, {data['address']['municipality']}, LEYTE",
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

@app.route("/gen_reports")
def gen_reports():
    return render_template("reports.html")

@app.route('/get_patient/<pin>')
def get_patient(pin):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.pin, pi.last_name, pi.first_name, pi.middle_name, pi.name_ext,
               pi.date_of_birth, pi.sex, pi.mobile,
               a.municipality, a.barangay
        FROM patients p
        LEFT JOIN personal_info pi ON pi.patient_id = p.id
        LEFT JOIN addresses a ON a.patient_id = p.id
        WHERE p.pin = %s
    """, (pin,))
    
    patient = cursor.fetchone()
    cursor.close()
    conn.close()

    if patient:
        return jsonify({"exists": True, **patient})
    else:
        return jsonify({"exists": False})
    
def dataTable():
#     SELECT COUNT(*) AS NumberOfMale
# FROM patients p
# LEFT JOIN personal_info pi ON pi.patient_id = p.id
# WHERE pi.sex = 'Male';

# SELECT COUNT(*) AS NumberOfFemale
# FROM patients p
# LEFT JOIN personal_info pi ON pi.patient_id = p.id
# WHERE pi.sex = 'Female';

# SELECT 
#     p.pin AS MemberPIN,
#     p.dependent_pin AS DependentPIN,
#     CONCAT(pi.last_name, ', ', pi.middle_name, ' ', pi.first_name, ' ', IFNULL(pi.name_ext, '')) AS Name,
#     a.municipality AS Municipality,
#     a.barangay AS Barangay,
#     pi.sex AS Sex
# FROM patients p
# LEFT JOIN personal_info pi ON pi.patient_id = p.id
# LEFT JOIN addresses a ON a.patient_id = p.id
# ORDER BY pi.last_name, pi.first_name;




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)