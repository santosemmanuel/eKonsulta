from pydoc import doc
from flask import Flask, render_template, request, jsonify, current_app, url_for, session, redirect, flash
from fillpdf import fillpdfs
from pdfrw import PdfReader as PdfRwReader, PdfWriter as PdfRwWriter, PageMerge, PdfDict, PdfName, PdfObject
from datetime import datetime, date
from pdf2image import convert_from_path
import pymysql
import pymysql.cursors
import os
import json
import traceback
# import mysql.connector
# import sqlite3
import base64
import fitz
import qrcode
from waitress import serve
from PyPDF2 import PdfReader, PdfWriter
from dotenv import load_dotenv
from db import get_db_connection
from zoneinfo import ZoneInfo
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io
from io import BytesIO
import cv2
import numpy as np
import tempfile

app = Flask(__name__)
app.secret_key = "MHOBurauen"
load_dotenv()
today = datetime.now(ZoneInfo("Asia/Manila")).date()

# ==========================
# CONFIG (EDIT HERE ONLY)
# ==========================
FRONT_X = 420
FRONT_Y = 390

BIRTH_CERT_X = 420
BIRTH_CERT_Y = 100

BACK_X = 420
BACK_Y = 200

BIRTH_CERT_MAX_WIDTH = 550
BIRTH_CERT_MAX_HEIGHT = 550
MAX_WIDTH = 280


def check_form_version(ses):
    return ".1" if ses else ""


def flatten_pdf(input_pdf_path, output_pdf_path=None):
    """
    Flatten a fillable PDF using pdfrw library.
    Merges form field content with the PDF background, making the form non-editable.

    Args:
        input_pdf_path: Path to the input PDF file
        output_pdf_path: Path for output (if None, overwrites input)

    Returns:
        Path to the flattened PDF
    """
    if output_pdf_path is None:
        output_pdf_path = input_pdf_path

    try:
        # Read the PDF
        template = PdfRwReader(input_pdf_path)

        # Flatten the PDF by merging annotations/form fields with the page content
        for page in template.pages:
            if page.Annots:
                # Remove annotations to flatten form fields
                page.Annots = None

        # Write the flattened PDF
        PdfRwWriter().write(output_pdf_path, template)
        print(f"PDF flattened successfully: {output_pdf_path}")
        return output_pdf_path
    except Exception as e:
        print(f"Error flattening PDF: {str(e)}")
        return None


@app.route("/")
def index():
    if "user" in session and session.get("position") == "user":
        pdf_files = [
            {"name": "EKAS EPRESS MCA",
                "url": f"/static/pdfs/user_{session.get('user_id')}/output/EKAS,EPRESS,MCA_OUTPUT_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf"},
            {"name": "PKRF CONSENT HEALTH SCREENING",
                "url": f"/static/pdfs/user_{session.get('user_id')}/output/PKRF,Consent, Health Screening_OUTPUT_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf"},
            {"name": "EMPANELMENT SLIP (MCA)",
                "url": f"/static/pdfs/user_{session.get('user_id')}/output/EMPANELMENT_(MCA)_OUTPUT_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf"},
        ]
        feature_enabled = session.get("feature_enabled", False)
        return render_template("index.html", pdf_files=pdf_files, user=session.get("user"), feature_enabled=feature_enabled)
    elif "position" in session and session.get("position") == "admin":
        return redirect(url_for("gen_reports"))
    elif "position" in session and session.get("position") == "scanner":
        return redirect(url_for("scannerPage"))
    else:
        flash("Please login first", "warning")
        return redirect(url_for("login"))


@app.route("/submit_form", methods=["POST"])
def submit_form():
    data = request.get_json()
    pretty_json_string = json.dumps(data, indent=4)
    patient_data = dict(data)
    print(pretty_json_string)

    # clean_files([f"user_{session.get('user_id')}/output/EKAS,EPRESS,MCA_OUTPUT_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf",
    #              f"user_{session.get('user_id')}/output/PKRF,Consent, Health Screening_OUTPUT_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf"])

    fill_EKAS_EPRESS_MCA(patient_data)
    fill_PKRF_CHS(patient_data)
    fill_MCA(patient_data)

    conn = get_db_connection()
    cursor = conn.cursor()
    user_id = session.get('user_id')

    # try:
    #     # 🔍 CHECK IF dependent_pin EXISTS
    #     cursor.execute(
    #         "SELECT id FROM patients WHERE dependent_pin = ? OR pin = ?",
    #         (patient_data["dependentPin"], patient_data["pin"])
    #     )

    #     existing_patient = cursor.fetchone()

    #     if not existing_patient:
    #         # 🆕 INSERT NEW RECORD
    #         insert_query = """
    #             INSERT INTO patients (patient_is_member, pin, dependent_pin, created_at)
    #             VALUES (?, ?, ?, ?)
    #         """

    #         cursor.execute(
    #             insert_query,
    #             (
    #                 patient_data["patientIsMember"],
    #                 patient_data["pin"],
    #                 patient_data["dependentPin"],
    #                 datetime.now()
    #             )
    #         )

    #         patient_id = cursor.lastrowid

    #         # 🧍 INSERT personal_info
    #         cursor.execute("""
    #             INSERT INTO personal_info
    #             (patient_id, last_name, first_name, middle_name, name_ext,
    #             date_of_birth, sex, mobile)
    #             VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    #         """, (
    #             patient_id,
    #             patient_data["personalInfo"]["lastName"],
    #             patient_data["personalInfo"]["firstName"],
    #             patient_data["personalInfo"]["middleName"],
    #             patient_data["personalInfo"]["nameExt"],
    #             patient_data["otherDetails"]["dob"],
    #             patient_data["otherDetails"]["sex"],
    #             patient_data["otherDetails"]["mobile"]
    #         ))

    #         # 🏠 INSERT address
    #         cursor.execute("""
    #             INSERT INTO addresses
    #             (patient_id, municipality, barangay)
    #             VALUES (?, ?, ?)
    #         """, (
    #             patient_id,
    #             patient_data["address"]["municipality"],
    #             patient_data["address"]["barangay"]
    #         ))

    #         insert_masterPatient_query = """
    #             INSERT INTO patients_master (user_id, patient_id, date_created)
    #             VALUES (?, ?, ?)
    #         """

    #         cursor.execute(
    #             insert_masterPatient_query,
    #             (user_id, patient_id, datetime.now())
    #         )

    #         conn.commit()

    #     else:

    #         patient_master = """
    #             SELECT id
    #             FROM patients_master
    #             WHERE patient_id = ?
    #             AND date(date_created) = date('now')
    #         """

    #         cursor.execute(
    #             patient_master,
    #             (existing_patient['id'],)
    #         )

    #         existing_patient_master = cursor.fetchone()

    #         if not existing_patient_master:
    #             insert_query = """
    #                 INSERT INTO patients_master (user_id, patient_id, date_created)
    #                 VALUES (?, ?, ?)
    #             """

    #             cursor.execute(
    #                 insert_query,
    #                 (user_id, existing_patient['id'], datetime.now())
    #             )

    #     conn.commit()

    # except sqlite3.Error as err:
    #     print(f"Error: {err}")
    #     return jsonify({"status": "error", "message": "Database query failed"}), 500

    # finally:
    #     cursor.close()
    #     conn.close()

    return jsonify({"status": "success", "message": "Form received"})


def fill_EKAS_EPRESS_MCA(data):

    philhealth = "✔" if data['transactionInfo']['philhealth'] == True else "✘"
    philsys = "✔" if data['transactionInfo']['philsys'] == True else "✘"
    pcu = "PCU Verification Failed"
    if data['transactionInfo']['transactionNumber'] != '':
        pcu = f"PCU Transaction Number: {data['transactionInfo']['transactionNumber']} \t\t PhilHealth: {philhealth} \t PhilSys: {philsys}"

    try:
        pdf_path = os.path.join(
            current_app.root_path, f"static/pdfs/user_{session.get('user_id')}/template/EKAS,EPRESS,MCA_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf")
        output_pdf = os.path.join(
            current_app.root_path, f"static/pdfs/user_{session.get('user_id')}/output/EKAS,EPRESS,MCA_OUTPUT_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf")
        form_fields_EKAS_EPRESS_MCA = list(
            fillpdfs.get_form_fields(pdf_path).keys())

        print(form_fields_EKAS_EPRESS_MCA)
        initials = session.get("initials")
        pin = data['pin']
        memberDependent = "Member"
        if data['patientIsMember'] == 'dependent':
            memberDependent = "Dependent"
            pin = data['dependentPin']

        date_object = datetime.strptime(
            data["otherDetails"]["dob"], "%Y-%m-%d")
        formatted_date = date_object.strftime('%m-%d-%Y')

        age = get_age_display(data["otherDetails"]["dob"])

        cellphoneNum = data["otherDetails"]["mobile"]
        patientMiddleName = (
            data["personalInfo"]["middleName"][0]
            if data["personalInfo"]["middleName"]
            else ""
        )
        patientFullName = f"{data['personalInfo']['firstName']} {patientMiddleName} {data['personalInfo']['lastName']} {data['personalInfo']['nameExt']}"

        member = "Yes" if data["patientIsMember"] == "member" else None
        dependent = "Yes" if data["patientIsMember"] == "dependent" else None
        representative = "" if not data["otherDetails"]["representative"] else data["otherDetails"]["representative"]
        reprelation = ""

        if data["otherDetails"]["relationship"] == "Others":
            reprelation = data["otherDetails"]["otherRelationship"]
        elif data["otherDetails"]["relationship"] != "-Select-":
            reprelation = data["otherDetails"]["relationship"]

        data_EKAS_EPRESS_MCA = {
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("PatientName")]: patientFullName,
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("DOB")]: formatted_date,
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("PIN")]: pin,
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("BenefitYear")]: today.year,
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("FullnameAndDateBeneficiary")]: f"{patientFullName}\t\t {today.month:02}/{today.day:02}/{today.year}",
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("Member")]: member,
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("Dependent")]: dependent,
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("Member1")]: member,
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("Dependent2")]: dependent,
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("ContactNum")]: cellphoneNum,
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("Age")]: age,
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("Performed")]: "Yes",
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index(
                "DatePerformed")]: f"{today.month:02}/{today.day:02}/{today.year}",
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("Representative")]: representative,
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("RepRelation")]: reprelation,
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index(
                "PCU")]: pcu,
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index(
                "UserInitial")]: initials
        }
        
        patient_data_qr = {
            "pin": pin,
            "ln": data["personalInfo"]["lastName"],
            "fN": data['personalInfo']['firstName'],
            "mN": data["personalInfo"]["middleName"],
            "ext": data["personalInfo"]["nameExt"],
            "bod": data["otherDetails"]["dob"],
            "MD": memberDependent,
            "genDate": f"{today.month:02}/{today.day:02}/{today.year}",
        }

        qr_patient = generate_qr_code(patient_data_qr)

        add_qr_to_pdf(
            pdf_path,
            output_pdf,
            qr_patient
        )

        fillpdfs.write_fillable_pdf(
            output_pdf, output_pdf, data_EKAS_EPRESS_MCA, flatten=False)

    except Exception as e:
        print(f"This is the error {e}")


def fill_PKRF_CHS(data):
    try:
        pdf_path = os.path.join(
            current_app.root_path, f"static/pdfs/user_{session.get('user_id')}/template/PKRF,Consent, Health Screening_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf")
        output_pdf = os.path.join(
            current_app.root_path, f"static/pdfs/user_{session.get('user_id')}/output/PKRF,Consent, Health Screening_OUTPUT_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf")
        form_fields_PKRF_Consent = list(
            fillpdfs.get_form_fields(pdf_path).keys())

        date_object = datetime.strptime(
            data["otherDetails"]["dob"], "%Y-%m-%d")
        formatted_date = date_object.strftime('%m-%d-%Y')
        initials = session.get('initials')
        age = get_age_display(data["otherDetails"]["dob"])

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
        representative = "" if not data["otherDetails"]["representative"] else data["otherDetails"]["representative"]
        reprelation = ""

        if data["otherDetails"]["relationship"] == "Others":
            reprelation = data["otherDetails"]["otherRelationship"]
        elif data["otherDetails"]["relationship"] != "-Select-":
            reprelation = data["otherDetails"]["relationship"]

        pin = data["pin"]
        if (data["patientIsMember"] == "dependent"):
            pin = data["dependentPin"]

        data_PKRF_CHS = {
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("Member")]: member,
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("Dependent")]: dependent,
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("PIN")]: pin,
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
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("MemberPIN")]: data.get('pin', ''),
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("DependentPIN")]: data.get('dependentPin', ''),
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("NameExt")]: data["personalInfo"]["nameExt"],
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("Age")]: age,
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("Gender")]: gender,
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("Representative")]: representative,
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index(
                "RepRelation")]: reprelation,
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index(
                "UserInitial")]: initials
        }

        fillpdfs.write_fillable_pdf(pdf_path, output_pdf, data_PKRF_CHS)
    except Exception as e:
        print(f"This is the error{e}")


def fill_MCA(data):
    try:

        philhealth = "✔" if data['transactionInfo']['philhealth'] == True else "✘"
        philsys = "✔" if data['transactionInfo']['philsys'] == True else "✘"
        pcu = "PCU Verification Failed"
        if data['transactionInfo']['transactionNumber'] != '':
            pcu = f"PCU Transaction Number: {data['transactionInfo']['transactionNumber']} \t\t PhilHealth: {philhealth} \t PhilSys: {philsys}"

        pdf_path = os.path.join(
            current_app.root_path, f"static/pdfs/user_{session.get('user_id')}/template/EMPANELMENT_(MCA)_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf")
        output_pdf = os.path.join(
            current_app.root_path, f"static/pdfs/user_{session.get('user_id')}/output/EMPANELMENT_(MCA)_OUTPUT_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf")
        form_fields_MCA = list(
            fillpdfs.get_form_fields(pdf_path).keys())
        # print(form_fields_EKAS_EPRESS_MCA)

        initials = session.get("initials")
        pin = data['pin']
        if data['patientIsMember'] == 'dependent':
            pin = data['dependentPin']

        date_object = datetime.strptime(
            data["otherDetails"]["dob"], "%Y-%m-%d")
        formatted_date = date_object.strftime('%m-%d-%Y')

        cellphoneNum = data["otherDetails"]["mobile"]
        patientMiddleName = (
            data["personalInfo"]["middleName"][0]
            if data["personalInfo"]["middleName"]
            else ""
        )
        patientFullName = f"{data['personalInfo']['firstName']} {patientMiddleName} {data['personalInfo']['lastName']} {data['personalInfo']['nameExt']}"

        member = "Yes" if data["patientIsMember"] == "member" else None
        dependent = "Yes" if data["patientIsMember"] == "dependent" else None
        representative = "" if not data["otherDetails"]["representative"] else data["otherDetails"]["representative"]
        reprelation = ""

        if data["otherDetails"]["relationship"] == "Others":
            reprelation = data["otherDetails"]["otherRelationship"]
        elif data["otherDetails"]["relationship"] != "-Select-":
            reprelation = data["otherDetails"]["relationship"]

        data_MCA = {
            form_fields_MCA[form_fields_MCA.index("PatientName")]: patientFullName,
            form_fields_MCA[form_fields_MCA.index("DOB")]: formatted_date,
            form_fields_MCA[form_fields_MCA.index("PIN")]: pin,
            form_fields_MCA[form_fields_MCA.index("BenefitYear")]: today.year,
            form_fields_MCA[form_fields_MCA.index("FullnameAndDateBeneficiary")]: f"{patientFullName}\t\t {today.month:02}/{today.day:02}/{today.year}",
            form_fields_MCA[form_fields_MCA.index("BenefitYear1")]: today.year - 1,
            form_fields_MCA[form_fields_MCA.index("Representative")]: representative,
            form_fields_MCA[form_fields_MCA.index("RepRelation")]: reprelation,
            form_fields_MCA[form_fields_MCA.index("PCU")]: pcu,
            form_fields_MCA[form_fields_MCA.index("UserInitial")]: initials
        }

        fillpdfs.write_fillable_pdf(
            pdf_path, output_pdf, data_MCA, flatten=False)
    except Exception as e:
        print(f"This is the error {e}")


def get_age_display(dob_string, format="%Y-%m-%d"):
    """
    Returns age in days, months, or years+months.
    Example input: '2025-09-10'
    """

    dob = datetime.strptime(dob_string, format).date()
    today = date.today()

    total_months = (today.year - dob.year) * 12 + (today.month - dob.month)

    if today.day < dob.day:
        total_months -= 1

    years = total_months // 12
    months = total_months % 12

    # --- Medical-friendly display ---
    if years == 0 and months == 0:
        days = (today - dob).days
        return f"{days} day(s) old"
    elif years == 0:
        return f"{months} month(s)"
    else:
        return years


def clean_files(file_list):
    for f in file_list:
        try:
            if os.path.exists(os.path.join(current_app.root_path, "static", "pdfs", f)):
                os.remove(os.path.join(
                    current_app.root_path, "static", "pdfs", f))
                print(f"Deleted {f}")
        except Exception as e:
            print(f"Error deleting {f}: {e}")


@app.route("/get_pdfs")
def get_pdfs():
    return jsonify([
        {
            "name": "EKAS EPRESS MCA",
            "url": url_for("static", filename=f"pdfs/user_{session.get('user_id')}/output/EKAS,EPRESS,MCA_OUTPUT_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf")
        },
        {
            "name": "PKRF CONSENT HEALTH SCREENING",
            "url": url_for("static", filename=f"pdfs/user_{session.get('user_id')}/output/PKRF,Consent, Health Screening_OUTPUT_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf")
        },
        {
            "name": "EMPANELMENT SLIP (MCA)",
            "url": url_for("static", filename=f"pdfs/user_{session.get('user_id')}/output/EMPANELMENT_(MCA)_OUTPUT_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf")
        },
    ])


@app.route("/gen_reports")
def gen_reports():

    # Maleresult = getMaleCount()
    # male_count = Maleresult["NumberOfMale"]

    # Femaleresult = getFemaleCount()
    # female_count = Femaleresult["NumberOfFemale"]

    cecRegistrationPatients = allPatientTable()
    transfereePatients = allTransferPatient()


    return render_template(
        "reports.html",
        male_count=0,
        female_count=0,
        cecRegistrationPatients=cecRegistrationPatients,
        transfereepatients=transfereePatients
    )

@app.route("/saveScanned", methods=["POST"])
def saveScanned():
    data = request.get_json()
    patientData = dict(data)
    conn = get_db_connection()

    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute(
            "SELECT id, pin FROM transmittal WHERE pin = %s",
            (patientData["pin"],)
        )
    
    existing = cursor.fetchone()

    if existing:
        pass
    else:
        cursor.execute("""
                INSERT INTO transmittal
                (
                    pin,
                    lastName,
                    firstName,
                    middleName,
                    ext,
                    birthday,
                    memberDepent,
                    generatedDate
                    dateScanned,
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                patientData["pin"],
                patientData["ln"],
                patientData["fN"],
                pcsf_data["Barangay"],
                pcsf_data["PIN"],
                mem_dep,
                pcu_transaction,
                datetime.now()
            ))

    print(data)


@app.route("/ActivityLogs")
def ActivityLogs():
    return render_template("activityLog.html")


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


def allPatientTable():
    conn = get_db_connection()
    cursor = conn.cursor()

    # cursor.execute("""
    #        SELECT * FROM cec_registration WHERE DateTimeProccess >= '2026-06-16'
    #         AND DateTimeProccess < '2026-06-16' + INTERVAL 1 DAY;
    # """)

    cursor.execute("""
           SELECT * FROM cec_registration
    """)
# FOR CUSTOM DATE RANGE
#     SELECT
#     p.pin AS MemberPIN,
#     p.dependent_pin AS DependentPIN,
#     CONCAT(pi.last_name, ', ', pi.middle_name, ' ', pi.first_name, ' ', IFNULL(pi.name_ext, '')) AS Name,
#     a.municipality AS Municipality,
#     a.barangay AS Barangay,
#     pi.sex AS Sex
# FROM patients_master pm
# LEFT JOIN patients p on pm.patient_id = p.id
# LEFT JOIN personal_info pi ON pi.patient_id = p.id
# LEFT JOIN addresses a ON a.patient_id = p.id WHERE pm.date_created >= '2026-01-15 00:00:00'
#   AND pm.date_created <  '2026-01-16 00:00:00';

    patients = cursor.fetchall()

    cursor.close()
    conn.close()

    return patients

def allTransferPatient():
    conn = get_db_connection()
    cursor = conn.cursor()

    # cursor.execute("""
    #        SELECT * FROM cec_registration WHERE DateTimeProccess >= '2026-06-16'
    #         AND DateTimeProccess < '2026-06-16' + INTERVAL 1 DAY;
    # """)

    cursor.execute("""
           SELECT * FROM cec_transfer
    """)
# FOR CUSTOM DATE RANGE
#     SELECT
#     p.pin AS MemberPIN,
#     p.dependent_pin AS DependentPIN,
#     CONCAT(pi.last_name, ', ', pi.middle_name, ' ', pi.first_name, ' ', IFNULL(pi.name_ext, '')) AS Name,
#     a.municipality AS Municipality,
#     a.barangay AS Barangay,
#     pi.sex AS Sex
# FROM patients_master pm
# LEFT JOIN patients p on pm.patient_id = p.id
# LEFT JOIN personal_info pi ON pi.patient_id = p.id
# LEFT JOIN addresses a ON a.patient_id = p.id WHERE pm.date_created >= '2026-01-15 00:00:00'
#   AND pm.date_created <  '2026-01-16 00:00:00';

    patients = cursor.fetchall()

    cursor.close()
    conn.close()

    return patients

def getMaleCount():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
            SELECT COUNT(*) AS NumberOfMale
            FROM patients_master pm
            LEFT JOIN patients p ON pm.patient_id = p.id
            LEFT JOIN personal_info pi ON pi.patient_id = p.id
            WHERE pi.sex = 'Male'
            AND pm.date_created >= '2026-01-28'
            AND pm.date_created < '2026-01-28' + INTERVAL 1 DAY;
    """)

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result


def getFemaleCount():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
           SELECT COUNT(*) AS NumberOfFemale
            FROM patients_master pm
            LEFT JOIN patients p ON pm.patient_id = p.id
            LEFT JOIN personal_info pi ON pi.patient_id = p.id
            WHERE pi.sex = 'Female'
            AND pm.date_created >= '2026-01-28'
            AND pm.date_created < '2026-01-28' + INTERVAL 1 DAY;
    """)

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result


def get_initials(full_name):
    words = full_name.split()
    initials = [word[0].upper() for word in words if word]
    return ".".join(initials)


@app.route("/login", methods=["GET", "POST"])
def login():
    try:
       
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            conn = get_db_connection()
            cursor = conn.cursor()

            query = "SELECT * FROM users WHERE username=%s AND password=%s"
            if os.getenv("USE_SQLITE") == 1:
                query = "SELECT * FROM users WHERE username=%s AND password=%s"

            cursor.execute(query, (username, password,))
            user = cursor.fetchone()
            print(user)
            name = user["firstName"] + " " + user["lastName"]

            if user:
                session["user_id"] = user["id"]
                session["user"] = user["username"]
                session["initials"] = get_initials(name)
                session["position"] = user["position"]
                flash("Login successful!", "success")
                return redirect(url_for("index"))
            else:
                flash("Invalid username or password", "danger")
                return redirect(url_for("login"))
                
        return render_template("login.html")
    # return render_template("maintenance.html")
    except Exception as e:
        print(e)

@app.route("/toggle", methods=["POST"])
def toggle():
    enabled = bool(request.json.get("enabled"))
    session["feature_enabled"] = enabled

    return jsonify({
        "status": "ok",
        "feature_enabled": enabled
    })


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/registration")
def registration():
    user_id = session.get('user_id')
    pdf_url = url_for(
            'static',
            filename=f"pdfs/user_{user_id}/output/PCSF_OUTPUT_user_{user_id}{check_form_version(session.get('feature_enabled', False))}.pdf"
        )
    ekass_epress_pdf = url_for('static', filename=f"pdfs/user_{session.get('user_id')}/output/EKAS,EPRESS,MCA_OUTPUT_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf")
    fpe_pdf = url_for('static', filename=f"pdfs/user_{session.get('user_id')}/output/PKRF,Consent, Health Screening_OUTPUT_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf")


    return render_template("registration.html", 
                           user=session.get("user"),
                           pdf_file=pdf_url,
                           fpe_file=fpe_pdf,
                           ekass_epress=ekass_epress_pdf)

def process_image(image_bytes, enhance=True):
    try:
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return image_bytes

        if enhance:
            # basic enhancements: bilateral filter, convert to LAB and apply CLAHE
            img = cv2.bilateralFilter(img, 9, 75, 75)

            # attempt document detection and perspective transform
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            edged = cv2.Canny(blur, 50, 150)

            contours, _ = cv2.findContours(
                edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(
                contours, key=cv2.contourArea, reverse=True)[:5]

            doc_cnt = None
            for c in contours:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.02 * peri, True)
                if len(approx) == 4:
                    doc_cnt = approx
                    break

            if doc_cnt is not None:
                # obtain a top-down view of the document
                pts = doc_cnt.reshape(4, 2)
                rect = np.zeros((4, 2), dtype="float32")

                s = pts.sum(axis=1)
                rect[0] = pts[np.argmin(s)]
                rect[2] = pts[np.argmax(s)]

                diff = np.diff(pts, axis=1)
                rect[1] = pts[np.argmin(diff)]
                rect[3] = pts[np.argmax(diff)]

                (tl, tr, br, bl) = rect
                widthA = np.sqrt(
                    ((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
                widthB = np.sqrt(
                    ((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
                maxWidth = max(int(widthA), int(widthB))

                heightA = np.sqrt(
                    ((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
                heightB = np.sqrt(
                    ((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
                maxHeight = max(int(heightA), int(heightB))

                dst = np.array([
                    [0, 0],
                    [maxWidth - 1, 0],
                    [maxWidth - 1, maxHeight - 1],
                    [0, maxHeight - 1]], dtype="float32")

                M = cv2.getPerspectiveTransform(rect, dst)
                warp = cv2.warpPerspective(
                    img, M, (maxWidth, maxHeight))
                img = warp

            # apply CLAHE for contrast
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            limg = cv2.merge((cl, a, b))
            img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        # encode back to PNG
        success, encoded = cv2.imencode(
            '.png', img, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        if success:
            return encoded.tobytes()
        return image_bytes
    except Exception:
        return image_bytes

def generate_qr_code(json_data):
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4
        )

        qr.add_data(json.dumps(json_data))
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return buffer.getvalue()
    except Exception as e:
        print(f"This is the qr error {e}")

def add_qr_to_pdf(input_pdf, output_pdf, qr_image_bytes):
    try:
        doc = fitz.open(input_pdf)

        page = doc[0]  # First page

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(qr_image_bytes)
            qr_path = tmp.name

        rect = fitz.Rect(
            210, 15,
            280, 85
        )

        page.insert_image(rect, filename=qr_path)

        doc.save(output_pdf)
        doc.close()
        
    except Exception as e:
        print(f"This is the qr error {e}")

@app.route("/submitCECRegistration", methods=["POST"])
def submitCECRegistration():
    # Handle registration submission logic here
    user_id = session.get('user_id')
    UPLOAD_FOLDER = os.path.join(
        current_app.root_path, f"static/pdfs/user_{user_id}/uploads")

    # Create the upload directory if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"status": "error", "message": "Invalid or missing JSON payload."}), 400

    try:
        data = dict(data)
    except Exception as e:
        print(f"Invalid JSON payload: {e}")
        return jsonify({"status": "error", "message": "Invalid JSON payload."}), 400

    pretty_json_string = json.dumps(data, indent=4)
    if user_id is None:
        return jsonify({"status": "error", "message": "User session is missing. Please log in again."}), 401

    try:
        pdf_path = os.path.join(
            current_app.root_path, f"static/pdfs/user_{user_id}/template/PCSF_user_{user_id}{check_form_version(session.get('feature_enabled', False))}.pdf")
        output_pdf = os.path.join(
            current_app.root_path, f"static/pdfs/user_{user_id}/output/PCSF_OUTPUT_user_{user_id}{check_form_version(session.get('feature_enabled', False))}.pdf")

        date_object = datetime.strptime(
            data["data"]["otherDetails"]["dob"], "%Y-%m-%d")
        formatted_date = date_object.strftime('%m-%d-%Y')
        initials = session.get('initials')
        age = get_age_display(data["data"]["otherDetails"]["dob"])

        gender = data["data"]["otherDetails"]['sex']
        patientMiddleName = (
            data["data"]["personalInfo"]["middleName"][0]
            if data["data"]["personalInfo"]["middleName"]
            else ""
        )
        patientFullName = f"{data['data']['personalInfo']['firstName']} {patientMiddleName} {data['data']['personalInfo']['lastName']} {data['data']['personalInfo']['nameExt']}"

        # NOTE: Checkboxes in pypdf require formatting like "/Yes" or "/Off"
        member = "Yes" if data["data"]["patientIsMember"] == "member" else ""
        dependent = "Yes" if data["data"]["patientIsMember"] == "dependent" else ""
        transfer = "Yes" if data["data"]["transfer"]["transfer"] == True else ""

        barangay = data["data"]["address"]["barangay"]
        municipality = data["data"]["address"]["municipality"]
        representative = "" if not data["data"]["otherDetails"][
            "representative"] else data["data"]["otherDetails"]["representative"]
        reprelation = ""

        if data["data"]["otherDetails"]["relationship"] == "Others":
            reprelation = data["data"]["otherDetails"]["otherRelationship"]
        elif data["data"]["otherDetails"]["relationship"] != "-Select-":
            reprelation = data["data"]["otherDetails"]["relationship"]

        pin = data["data"]["pin"]
        if (data["data"]["patientIsMember"] == "dependent"):
            pin = data["data"]["dependentPin"]

        doc = fitz.open(pdf_path)

        pcsf_data = {
            "Member": member,
            "Dependent": dependent,
            "PIN": pin,
            "DateToday": f"{today.month:02}/{today.day:02}/{today.year}",
            "LastName": data["data"]["personalInfo"]["lastName"],
            "FirstName": data["data"]["personalInfo"]["firstName"],
            "MiddleName": data["data"]["personalInfo"]["middleName"],
            "Barangay": barangay.upper(),
            "Municipality": municipality.upper(),
            "Province": "LEYTE",
            "DOB": formatted_date,
            "ContactNum": data["data"]["otherDetails"]["mobile"],
            "PatientSignature": patientFullName,
            "Representative": representative,
            "RepRelation": reprelation,
            "PatientSignOverPrinted": patientFullName,
            "PCUTransactionCode": data['data']['transactionInfo']['transactionNumber'],
            "Transfer": transfer,
            "PreviousPCC": data['data']['transfer']['previousPCC']
        }

        fill_PKRF_CHS(data["data"])
        fill_EKAS_EPRESS_MCA(data["data"])

        for page in doc:
            widgets = page.widgets()

        if widgets:
            for widget in widgets:
                field_name = widget.field_name

                if field_name in pcsf_data:
                    widget.field_value = pcsf_data[field_name]
                    widget.update()

        # Flatten form
            # for page in doc:
            #     widgets = list(page.widgets() or [])

            #     for widget in widgets:
            #         rect = widget.rect
            #         value = widget.field_value or ""

            #         # Write value as normal page text
            #         if widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
            #             if value == "Yes":
            #                 page.insert_text(
            #                     (rect.x0 + 2, rect.y1 - 2),
            #                     "/",
            #                     fontsize=8,
            #                 )
            #         elif widget.field_name == "PatientSignOverPrinted":
            #             page.insert_text(
            #                 (rect.x0 + 2, rect.y1 - 2),
            #                 str(value),
            #                 fontsize=15,
            #             )
            #         else:
            #             page.insert_text(
            #                 (rect.x0 + 2, rect.y1 - 2),
            #                 str(value),
            #                 fontsize=8,
            #             )

            #         # Remove form field
            #         page.delete_widget(widget)
            for page in doc:
                widgets = list(page.widgets() or [])

                for widget in widgets:
                    rect = widget.rect
                    value = widget.field_value or ""

                    # 1. Handle Checkbox Fields
                    if widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                        if value == "Yes":
                            check_symbol = "X"
                            font_name = "helv"
                            # Dynamic scaling based on box size
                            font_size = min(rect.width, rect.height) * 0.85

                            # Center the checkmark horizontally and vertically inside the box
                            symbol_width = fitz.get_text_length(
                                check_symbol, fontname=font_name, fontsize=font_size)
                            adjusted_x = rect.x0 + \
                                ((rect.width - symbol_width) / 2.0)
                            adjusted_y = rect.y1 - \
                                ((rect.height - font_size) / 2.0) - \
                                (font_size * 0.1)

                            page.insert_text(
                                (adjusted_x, adjusted_y),
                                check_symbol,
                                fontsize=font_size,
                                fontname=font_name,
                            )

                    # 2. Handle the Patient Signature Field (Centered & Auto-Sized)
                    elif widget.field_name == "PatientSignOverPrinted":
                        if value:
                            font_name = "helv"
                            font_size = 15.0  # Your preferred maximum starting font size
                            min_size = 6.0

                            # Auto-size logic: Reduce font size until the signature fits within the box width
                            while font_size >= min_size:
                                text_width = fitz.get_text_length(
                                    str(value), fontname=font_name, fontsize=font_size)
                                if text_width <= rect.width:
                                    break
                                font_size -= 0.5

                            # Center the signature text horizontally and vertically inside the box
                            adjusted_x = rect.x0 + \
                                ((rect.width - text_width) / 2.0)
                            adjusted_y = rect.y1 - \
                                ((rect.height - font_size) / 2.0) - \
                                (font_size * 0.05)

                            page.insert_text(
                                (adjusted_x, adjusted_y),
                                str(value),
                                fontsize=font_size,
                                fontname=font_name,
                            )

                    # 3. Handle Fallback for All Other Text Fields (Left-aligned)
                    else:
                        if value:
                            # Vertically centers the text row within your fallback box height
                            font_size = 8.0
                            adjusted_y = rect.y1 - \
                                ((rect.height - font_size) / 2.0) - \
                                (font_size * 0.05)

                            page.insert_text(
                                (rect.x0 + 2, adjusted_y),
                                str(value),
                                fontsize=font_size,
                            )

                    # Remove interactive form field element from the page layout canvas
                    page.delete_widget(widget)
        doc.save(output_pdf)
        doc.close()

        print("PDF filled and flattened successfully.")
        # --- PYPDF WRITE START ---
        # Apply data to fields

        # Make sure output directory exists
        os.makedirs(os.path.dirname(output_pdf), exist_ok=True)

        # Save data to output path
        # with open(output_pdf, "wb") as output_file:
        #     writer.write(output_file)

        front_image = data.get("front")
        back_image = data.get("back")
        birth_certificate = data.get("birthCertificate")

        if birth_certificate:
            #code here
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            birth_filename = f"{UPLOAD_FOLDER}/birth_certificate_{timestamp}.png"

            # ==========================
            # DECODE BASE64
            # ==========================
            birth_bytes = base64.b64decode(birth_certificate.split(",")[1])

            # Reuse your existing process_image() function
            processed_birth = process_image(birth_bytes)

            # Save processed image
            with open(birth_filename, "wb") as f:
                f.write(processed_birth)

            if not os.path.exists(output_pdf):
                return jsonify({"status": "error", "message": "PCSF.pdf"}), 500

            reader = PdfReader(output_pdf)
            writer = PdfWriter()

            writer.append(reader)

            def make_overlay(image_bytes, page_width, page_height, x=None, y=None, max_width=400, max_height=400, rotation=0):

                packet = io.BytesIO()
                c = canvas.Canvas(packet, pagesize=(page_width, page_height))

                img = ImageReader(io.BytesIO(image_bytes))
                iw, ih = img.getSize()

                # Scale to fit within max_width and max_height
                scale = min(
                    max_width / iw,
                    max_height / ih
                )

                draw_w = iw * scale
                draw_h = ih * scale

                if x is None:
                    x = (page_width - draw_w) / 2

                if y is None:
                    y = (page_height - draw_h) / 2

                c.saveState()

                if rotation == -90:  # clockwise
                    c.translate(x, y + draw_w)
                elif rotation == 90:  # counter-clockwise
                    c.translate(x + draw_h, y)
                elif rotation == 180:
                    c.translate(x + draw_w, y + draw_h)
                else:
                    c.translate(x, y)

                c.rotate(rotation)

                c.drawImage(
                    img,
                    0,
                    0,
                    width=draw_w,
                    height=draw_h
                )

                c.restoreState()

                c.save()
                packet.seek(0)

                return PdfReader(packet).pages[0]

            out_path = os.path.join(
                current_app.root_path,
                f"static/pdfs/user_{user_id}/output/PCSF_temp_birth_{timestamp}.pdf"
            )

            final_path = output_pdf

            try:

                # ====================================
                # ADD BIRTH CERTIFICATE TO PAGE 1
                # ====================================
                page = reader.pages[0]

                pw = float(page.mediabox.width)
                ph = float(page.mediabox.height)

                overlay_birth = make_overlay(
                    birth_bytes,
                    pw,
                    ph,
                    x=BIRTH_CERT_X,      # define these constants
                    y=BIRTH_CERT_Y,
                    max_width=BIRTH_CERT_MAX_WIDTH,
                    max_height=BIRTH_CERT_MAX_HEIGHT,
                    rotation=-90
                )

                page.merge_page(overlay_birth)

                writer.add_page(page)

                # Save
                with open(out_path, "wb") as f:
                    writer.write(f)

                os.replace(out_path, final_path)

                doc = fitz.open(output_pdf)
                doc.delete_page(0)
                doc.saveIncr()
                doc.close()

                try:
                    os.remove(birth_filename)
                except OSError:
                    pass

            except Exception as e:
                print(f"PDF processing error: {e}")
                return jsonify({
                    "status": "error",
                    "message": f"PDF processing error: {e}"
                }), 500
        else:

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            front_filename = f"{UPLOAD_FOLDER}/front_{timestamp}.png"
            back_filename = f"{UPLOAD_FOLDER}/back_{timestamp}.png"

            # ==========================
            # DECODE BASE64
            # ==========================
            front_bytes = base64.b64decode(front_image.split(",")[1])
            back_bytes = base64.b64decode(back_image.split(",")[1])

            processed_front = process_image(front_bytes)
            processed_back = process_image(back_bytes)

            # Save processed images
            with open(front_filename, "wb") as f:
                f.write(processed_front)

            with open(back_filename, "wb") as f:
                f.write(processed_back)

            if not os.path.exists(output_pdf):
                return jsonify({"status": "error", "message": "PCSF.pdf"}), 500

            reader = PdfReader(output_pdf)
            writer = PdfWriter()

            writer.append(reader)

            def make_overlay(image_bytes, page_width, page_height,
                            x=None, y=None, max_width=250):

                packet = io.BytesIO()
                c = canvas.Canvas(packet, pagesize=(page_width, page_height))

                img = ImageReader(io.BytesIO(image_bytes))
                iw, ih = img.getSize()

                # scale image
                scale = min(
                    max_width / iw,
                    page_height / ih
                )

                draw_w = iw * scale
                draw_h = ih * scale

                # ==========================
                # POSITION CONTROL
                # ==========================
                if x is None or x == 0:
                    x = page_width - draw_w - 20  # RIGHT SIDE DEFAULT

                if y is None:
                    y = (page_height - draw_h) / 2

                c.drawImage(img, x, y, width=draw_w, height=draw_h)
                c.save()

                packet.seek(0)
                return PdfReader(packet).pages[0]

            out_path = os.path.join(
                current_app.root_path, f"static/pdfs/user_{user_id}/output/PCSF_temp_{timestamp}.pdf")
            final_path = output_pdf

            try:

                # ==========================
                # PAGE 1 ONLY (IMPORTANT)
                # ==========================
                page = reader.pages[0]

                pw = float(page.mediabox.width)
                ph = float(page.mediabox.height)

                # FRONT ID (TOP RIGHT)
                overlay_front = make_overlay(
                    front_bytes,
                    pw,
                    ph,
                    x=FRONT_X,
                    y=FRONT_Y,
                    max_width=MAX_WIDTH
                )

                # BACK ID (BOTTOM RIGHT)
                overlay_back = make_overlay(
                    back_bytes,
                    pw,
                    ph,
                    x=BACK_X,
                    y=BACK_Y,
                    max_width=MAX_WIDTH
                )

                page.merge_page(overlay_front)
                page.merge_page(overlay_back)

                writer.add_page(page)

                # ==========================
                # SAVE OUTPUT
                # ==========================
                with open(out_path, "wb") as f:
                    writer.write(f)

                # replace original PDF with the updated file
                os.replace(out_path, final_path)

                doc = fitz.open(output_pdf)
                doc.delete_page(0)
                doc.saveIncr()
                doc.close()

                # delete temporary uploaded files after PDF creation
                try:
                    os.remove(front_filename)
                except OSError:
                    pass
                try:
                    os.remove(back_filename)
                except OSError:
                    pass

            except Exception as e:
                print(f"PDF processing error: {e}")
                return jsonify({"status": "error", "message": f"PDF processing error: {e}"}), 500
            
    except Exception as e:
        # return jsonify({"status": "error", "message": str(e)}), 500
        print(f"This is the error{e}")
        traceback.print_exc()

    try:
        conn = get_db_connection()

        cursor = conn.cursor(pymysql.cursors.DictCursor)

        pdf_url = url_for(
            'static',
            filename=f"pdfs/user_{user_id}/output/PCSF_OUTPUT_user_{user_id}{check_form_version(session.get('feature_enabled', False))}.pdf"
        )


        mem_dep = (
            "Member"
            if pcsf_data["Member"] == "Yes"
            else "Dependent"
            if pcsf_data["Dependent"] == "Yes"
            else "N/A"
        )

        pcu_transaction = pcsf_data.get("PCUTransactionCode") or "N/A"

        # Check if PIN exists
        cursor.execute(
            "SELECT id, PIN FROM cec_registration WHERE PIN = %s",
            (pcsf_data["PIN"],)
        )

        existing = cursor.fetchone()

        if existing:
            return jsonify({
                "success": False,
                "message": "Record already exists",
                "data": existing,
                "pdf_url": pdf_url
            }), 409

        # Insert record
        if pcsf_data["Transfer"] == "Yes":
            cursor.execute("""
                INSERT INTO cec_transfer
                (
                    LastName,
                    FirstName,
                    MiddleName,
                    Barangay,
                    PIN,
                    MemDep,
                    PCUTransaction,
                    DateTimeProccess
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                pcsf_data["LastName"],
                pcsf_data["FirstName"],
                pcsf_data["MiddleName"],
                pcsf_data["Barangay"],
                pcsf_data["PIN"],
                mem_dep,
                pcu_transaction,
                datetime.now()
            ))
        else:
            cursor.execute("""
                INSERT INTO cec_registration
                (
                    LastName,
                    FirstName,
                    MiddleName,
                    Barangay,
                    PIN,
                    MemDep,
                    PCUTransaction,
                    DateTimeProccess
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                pcsf_data["LastName"],
                pcsf_data["FirstName"],
                pcsf_data["MiddleName"],
                pcsf_data["Barangay"],
                pcsf_data["PIN"],
                mem_dep,
                pcu_transaction,
                datetime.now()
            ))

        conn.commit()
        
        fpe_pdf = url_for('static', filename=f"pdfs/user_{session.get('user_id')}/output/PKRF,Consent, Health Screening_OUTPUT_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf")
        ekass_epress_pdf = url_for('static', filename=f"pdfs/user_{session.get('user_id')}/output/EKAS,EPRESS,MCA_OUTPUT_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf")

        return jsonify({
            "success": True,
            "message": "Record inserted successfully",
            "inserted_id": cursor.lastrowid,
            "pdf_url": {"pcsf": pdf_url, "fpe": fpe_pdf, "ekass_epress": ekass_epress_pdf}
        }), 200

    except pymysql.MySQLError as e:
        return jsonify({
            "success": False,
            "message": f"MySQL Error: {str(e)}"
        }), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if 'cursor' in locals():
            cursor.close()

        if 'conn' in locals():
            conn.close()

@app.route("/scanner")
def scannerPage():
    return render_template("scanner.html")
if __name__ == '__main__':
    # from waitress import serve
    # serve(app, host="0.0.0.0", port=8180)
    app.run(host='0.0.0.0', port=8180, debug=True)
