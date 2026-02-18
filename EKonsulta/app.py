from flask import Flask, render_template, request, jsonify, current_app, url_for, session, redirect, flash
from fillpdf import fillpdfs
from pdfrw import PdfReader as PdfRwReader, PdfWriter as PdfRwWriter, PageMerge, PdfDict, PdfName
from datetime import datetime, date
from pdf2image import convert_from_path
import os
import json
import mysql.connector
# import cv2
# import numpy as np
from dotenv import load_dotenv
from db import get_db_connection
from zoneinfo import ZoneInfo

app = Flask(__name__)
app.secret_key = "MHOBurauen"
load_dotenv()
today = datetime.now(ZoneInfo("Asia/Manila")).date()

def check_form_version(ses):
    return ".1" if ses else ""


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
    cursor = conn.cursor(dictionary=True)
    user_id = session.get('user_id')

    try:
        # 🔍 CHECK IF dependent_pin EXISTS
        cursor.execute(
            "SELECT id FROM patients WHERE dependent_pin = %s or pin = %s",
            (patient_data["dependentPin"], patient_data["pin"])
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

            insert_masterPatient_query = """INSERT INTO patients_master (user_id, patient_id, date_created)
                    VALUES (%s, %s, %s)
                """
            cursor.execute(insert_masterPatient_query,
                           (user_id, patient_id, datetime.now()))
            conn.commit()
        else:

            patient_master = """SELECT id 
                FROM patients_master 
                WHERE patient_id = %s 
                AND date_created >= CURDATE() 
                AND date_created < CURDATE() + INTERVAL 1 DAY"""
            cursor.execute(patient_master,
                           (existing_patient['id'],)
                           )

            existing_patient_master = cursor.fetchone()

            if not existing_patient_master:
                insert_query = """INSERT INTO patients_master (user_id, patient_id, date_created)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(
                    insert_query, (user_id, existing_patient['id'], datetime.now()))
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
        pdf_path = os.path.join(
            current_app.root_path, f"static/pdfs/user_{session.get('user_id')}/template/EKAS,EPRESS,MCA_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf")
        output_pdf = os.path.join(
            current_app.root_path, f"static/pdfs/user_{session.get('user_id')}/output/EKAS,EPRESS,MCA_OUTPUT_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf")
        form_fields_EKAS_EPRESS_MCA = list(
            fillpdfs.get_form_fields(pdf_path).keys())

        print(form_fields_EKAS_EPRESS_MCA)
        pin = data['pin']
        if data['patientIsMember'] == 'dependent':
            pin = data['dependentPin']

        date_object = datetime.strptime(
            data["otherDetails"]["dob"], "%Y-%m-%d")
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
            form_fields_EKAS_EPRESS_MCA[form_fields_EKAS_EPRESS_MCA.index("RepRelation")]: reprelation
        }

        fillpdfs.write_fillable_pdf(
            pdf_path, output_pdf, data_EKAS_EPRESS_MCA, flatten=False)
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
            form_fields_PKRF_Consent[form_fields_PKRF_Consent.index("RepRelation")]: reprelation
        }

        fillpdfs.write_fillable_pdf(pdf_path, output_pdf, data_PKRF_CHS)
    except Exception as e:
        print(f"This is the error{e}")


def fill_MCA(data):
    try:
        pdf_path = os.path.join(
            current_app.root_path, f"static/pdfs/user_{session.get('user_id')}/template/EMPANELMENT_(MCA)_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf")
        output_pdf = os.path.join(
            current_app.root_path, f"static/pdfs/user_{session.get('user_id')}/output/EMPANELMENT_(MCA)_OUTPUT_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf")
        form_fields_MCA = list(
            fillpdfs.get_form_fields(pdf_path).keys())
        # print(form_fields_EKAS_EPRESS_MCA)
        pin = data['pin']
        if data['patientIsMember'] == 'dependent':
            pin = data['dependentPin']

        date_object = datetime.strptime(
            data["otherDetails"]["dob"], "%Y-%m-%d")
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
        }

        fillpdfs.write_fillable_pdf(
            pdf_path, output_pdf, data_MCA, flatten=False)
    except Exception as e:
        print(f"This is the error {e}")


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

    Maleresult = getMaleCount()
    male_count = Maleresult["NumberOfMale"]

    Femaleresult = getFemaleCount()
    female_count = Femaleresult["NumberOfFemale"]

    patients = allPatientTable()

    return render_template(
        "reports.html",
        male_count=male_count,
        female_count=female_count,
        patients=patients
    )


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
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
           SELECT 
    p.pin AS MemberPIN,
    p.dependent_pin AS DependentPIN,
    CONCAT(pi.last_name, ', ', pi.middle_name, ' ', pi.first_name, ' ', IFNULL(pi.name_ext, '')) AS Name,
    a.municipality AS Municipality,
    a.barangay AS Barangay,
    pi.sex AS Sex
FROM patients_master pm
LEFT JOIN patients p on pm.patient_id = p.id
LEFT JOIN personal_info pi ON pi.patient_id = p.id
LEFT JOIN addresses a ON a.patient_id = p.id WHERE pm.date_created >= '2026-01-28'
            AND pm.date_created < '2026-01-28' + INTERVAL 1 DAY;
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


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()

        if user:
            session["user_id"] = user['id']
            session["user"] = user['name']
            session["position"] = user["position"]
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")


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


if __name__ == '__main__':
    # from waitress import serve
    # serve(app, host="0.0.0.0", port=8080)
    app.run(host='0.0.0.0', port=8080, debug=True)
