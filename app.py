from flask import Flask, render_template, request, jsonify, current_app, url_for, session, redirect, flash
from datetime import datetime
import gc
import json
import os
import traceback
from collections import OrderedDict
from zoneinfo import ZoneInfo

import fitz
import pymysql
import pymysql.cursors
import shutil
from dotenv import load_dotenv

try:
    from waitress import serve
    # comment out if in production if not or in developement do not comment out
    serve = None
except ImportError:  # pragma: no cover - optional in local development
    serve = None

from models.db import get_db_connection
from models.pdf_fillers import fill_EKAS_EPRESS_MCA, fill_PKRF_CHS, fill_MCA
from models.reports import (
    allPatientTable,
    allTransferPatient,
    getCECRegistrationCount,
    getTransferreeCount,
    getEkassEpressTransmittal,
)
from utils.helper import (
    check_form_version,
    get_age_display,
    get_initials,
    convert_to_sql_date,
    attach_images_to_pdf,
)

app = Flask(__name__)
app.secret_key = "MHOBurauen"
load_dotenv()
today = datetime.now(ZoneInfo("Asia/Manila")).date()

# ==========================
# CONFIGURATION
# ==========================
FRONT_X = 420
FRONT_Y = 390

BIRTH_CERT_X = 430
BIRTH_CERT_Y = 100

BACK_X = 420
BACK_Y = 200

BIRTH_CERT_MAX_WIDTH = 490
BIRTH_CERT_MAX_HEIGHT = 700
MAX_WIDTH = 280


def build_pdf_url(user_id, filename):
    """Build a static URL for a generated PDF file."""
    return url_for("static", filename=f"pdfs/user_{user_id}/output/{filename}")


def get_current_user_pdf_urls(user_id):
    """Return the generated PDF URLs for the current user."""
    suffix = check_form_version(session.get("feature_enabled", False))
    return {
        "pcsf": build_pdf_url(user_id, f"PCSF_OUTPUT_user_{user_id}{suffix}.pdf"),
        "ekass_epress": build_pdf_url(user_id, f"EKAS,EPRESS,MCA_OUTPUT_user_{user_id}{suffix}.pdf"),
        "fpe": build_pdf_url(user_id, f"PKRF,Consent, Health Screening_OUTPUT_user_{user_id}{suffix}.pdf"),
        "mca": build_pdf_url(user_id, f"EMPANELMENT_(MCA)_OUTPUT_user_{user_id}{suffix}.pdf"),
    }



@app.route("/")
def index():
    if "user" in session and session.get("position") == "user":
        pdf_urls = get_current_user_pdf_urls(session.get("user_id"))
        pdf_files = [
            {"name": "EKAS EPRESS MCA", "url": pdf_urls["ekass_epress"]},
            {"name": "PKRF CONSENT HEALTH SCREENING", "url": pdf_urls["fpe"]},
            {"name": "EMPANELMENT SLIP (MCA)", "url": pdf_urls["mca"]},
        ]
        feature_enabled = session.get("feature_enabled", False)
        return render_template(
            "index.html",
            pdf_files=pdf_files,
            user=session.get("user"),
            feature_enabled=feature_enabled,
        )
    elif "position" in session and session.get("position") == "admin":
        return redirect(url_for("gen_reports"))
    elif "position" in session and session.get("position") == "scanner":
        return redirect(url_for("scannerPage"))
    else:
        # return render_template("maintenance.html")
        # flash("Please login first", "warning")
        return redirect(url_for("login"))


@app.route("/submit_form", methods=["POST"])
def submit_form():
    data = request.get_json(silent=True) or {}
    patient_data = dict(data)

    print(json.dumps(patient_data, indent=4))

    # Keep the PDF generation logic in the model layer and return the generated URL.
    fill_EKAS_EPRESS_MCA(patient_data)

    user_id = session.get("user_id") or "None"
    pdf_urls = get_current_user_pdf_urls(user_id)

    return jsonify({
        "success": True,
        "message": "Form submitted and PDFs generated successfully.",
        "pdf_url": {
            "ekass_epress": pdf_urls["ekass_epress"],
        },
    }), 200

@app.route("/get_pdfs")
def get_pdfs():
    pdf_urls = get_current_user_pdf_urls(session.get("user_id"))
    return jsonify([
        {"name": "EKAS EPRESS MCA", "url": pdf_urls["ekass_epress"]},
        {"name": "PKRF CONSENT HEALTH SCREENING", "url": pdf_urls["fpe"]},
        {"name": "EMPANELMENT SLIP (MCA)", "url": pdf_urls["mca"]},
    ])

@app.route("/gen_reports")
def gen_reports():

    # Maleresult = getMaleCount()
    # male_count = Maleresult["NumberOfMale"]

    # Femaleresult = getFemaleCount()
    # female_count = Femaleresult["NumberOfFemale"]

    cecRegistrationPatients = allPatientTable()
    transfereePatients = allTransferPatient()
    registrationCount = getCECRegistrationCount()
    transferreeCount = getTransferreeCount()
    ekassEpressTransmittal = getEkassEpressTransmittal()

    return render_template(
        "reports.html",
        male_count=0,
        female_count=0,
        cecRegistrationPatients=cecRegistrationPatients,
        transfereepatients=transfereePatients,
        cecRegCount = registrationCount,
        transferreeCount = transferreeCount,
        ekassEpressTransmittal = ekassEpressTransmittal
    )


@app.route("/saveScanned", methods=["POST"])
def saveScanned():
    try:
        data = request.get_json(silent=True) or {}
        patient_data = dict(data)
        conn = get_db_connection()

        if conn is None:
            return jsonify({"success": False, "message": "Database connection is unavailable."}), 500

        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            "SELECT id, pin FROM transmittal WHERE pin = %s AND DATE(dateScanned) = CURDATE()",
            (patient_data["pin"],),
        )

        existing = cursor.fetchone()
        if existing:
            return jsonify({"success": False, "message": "Record already exists for today."}), 409

        cursor.execute(
            """
            INSERT INTO transmittal
            (
                pin,
                lastName,
                firstName,
                middleName,
                ext,
                birthday,
                memberDepent,
                generatedDate,
                dateScanned
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                patient_data["pin"],
                patient_data["ln"],
                patient_data["fN"],
                patient_data["mN"],
                patient_data["ext"],
                patient_data["bod"],
                patient_data["MD"],
                convert_to_sql_date(patient_data["genDate"]),
                datetime.now(),
            ),
        )

        conn.commit()
        return jsonify({
            "success": True,
            "message": "Record inserted successfully",
            "inserted_id": patient_data,
        }), 200
    except Exception as exc:
        print(str(exc))
        return jsonify({"success": False, "message": str(exc)}), 500

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

@app.route('/getTransmittalData')
def getTransmittalData():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            pin,
            lastName,
            firstName,
            middleName,
            ext,
            DATE(dateScanned) AS scanDate
        FROM transmittal
        ORDER BY scanDate DESC, lastName, firstName;     
    """)

    rows = cursor.fetchall()

    grouped = OrderedDict()

    for row in rows:

        date = row["scanDate"].strftime("%d/%m/%Y")

        fullname = " ".join(filter(None, [
            row["lastName"],
            row["firstName"],
            row["middleName"],
            row["ext"]
        ])).upper()

        if date not in grouped:
            grouped[date] = []

        grouped[date].append(fullname)

    return jsonify(grouped)

@app.route("/login", methods=["GET", "POST"])
def login():
    try:
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            conn = get_db_connection()
            if conn is None:
                flash("Database connection is unavailable.", "danger")
                return redirect(url_for("login"))

            cursor = conn.cursor(pymysql.cursors.DictCursor)
            query = "SELECT * FROM users WHERE username=%s AND password=%s"
            cursor.execute(query, (username, password))
            user = cursor.fetchone()

            if user:
                if user["status"] == 1:
                    full_name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
                    session["user_id"] = user["id"]
                    session["user"] = user["username"]
                    session["initials"] = get_initials(full_name)
                    session["position"] = user["position"]
                    flash("Login successful!", "success")
                    return redirect(url_for("index"))
                else:
                    flash("This Account needs to be activated by Admin.", "warning")
                    return redirect(url_for("login"))
                        
            flash("Invalid username or password ", "danger")
            return redirect(url_for("login"))
        
        # For Maintenance
        # elif request.method == "GET":
        #     value = request.args.get('value')
        #     if value == "tempLogin":
        #         return render_template("login.html")

        return render_template("login.html")
        # return render_template("maintenance.html")
    except Exception as exc:
        print(exc)
        flash("An unexpected error occurred. Please try again.", "danger")
        return redirect(url_for("login"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    try:
        
        if request.method == "POST":

            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")

            # Basic validation
            if not first_name or not last_name:
                flash("First name and last name are required.", "danger")
                return redirect(url_for("signup"))

            if len(username) < 4:
                flash("Username must be at least 4 characters long.", "danger")
                return redirect(url_for("signup"))

            if len(password) < 6:
                flash("Password must be at least 6 characters long.", "danger")
                return redirect(url_for("signup"))

            if password != confirm_password:
                flash("Passwords do not match.", "danger")
                return redirect(url_for("signup"))

            conn = None
            cursor = None

            
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if username already exists
            cursor.execute(
                "SELECT id FROM users WHERE username = %s",
                (username,)
            )

            existing_user = cursor.fetchone()

            if existing_user:
                flash("Username already exists.", "danger")
                return redirect(url_for("signup"))

            # Hash password
            # hashed_password = generate_password_hash(password)

            # Default values
            position = "user"
            status = 0

            # Insert user
            cursor.execute("""
                INSERT INTO users
                (firstName, lastName, username, password, position, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                first_name,
                last_name,
                username,
                password,
                position,
                status
            ))

            # Get the newly created user's ID
            user_id = cursor.lastrowid

            # Create user's PDF folder
            user_folder = os.path.join(
                app.root_path,
                "static",
                "pdfs",
                f"user_{user_id}"
            )

            os.makedirs(user_folder, exist_ok=True)

            # User folder
            user_folder = os.path.join(
                app.root_path,
                "static",
                "pdfs",
                f"user_{user_id}"
            )

            # Create user folder
            os.makedirs(user_folder, exist_ok=True)

            # Create output and template folders
            user_output_folder = os.path.join(user_folder, "output")
            user_template_folder = os.path.join(user_folder, "template")

            os.makedirs(user_output_folder, exist_ok=True)
            os.makedirs(user_template_folder, exist_ok=True)


            # =========================
            # SAMPLE FOLDERS
            # =========================

            sample_folder = os.path.join(
                app.root_path,
                "static",
                "pdfs",
                "sample"
            )

            sample_template_folder = os.path.join(sample_folder, "template")


            # =========================
            # COPY TEMPLATE PDFs
            # =========================

            if os.path.exists(sample_template_folder):
                for filename in os.listdir(sample_template_folder):

                    if filename.lower().endswith(".pdf"):

                        source_file = os.path.join(
                            sample_template_folder,
                            filename
                        )

                        # Get original filename without .pdf
                        original_name = os.path.splitext(filename)[0]

                        # Example:
                        # template1_123.pdf
                        new_filename = f"{original_name}_{user_id}.pdf"

                        destination_file = os.path.join(
                            user_template_folder,
                            new_filename
                        )

                        shutil.copy2(
                            source_file,
                            destination_file
                        )

            # Commit database changes
            conn.commit()

            flash(
                "Registration successful! Your account is waiting for admin activation.",
                "success"
            )
            conn.close()

            return redirect(url_for("login"))

        return render_template("signup.html")
    
    except Exception as exc:
        print(exc)

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

@app.route("/registration", methods=["GET"])
def registration():
    value = request.args.get('value')
    user_id = session.get('user_id')
    pdf_urls = get_current_user_pdf_urls(user_id)

    match value:
        case "registration":
            # Handle registration logic
            return render_template(
                "registration.html",
                user=session.get("user"),
                pdf_file=pdf_urls["pcsf"],
                fpe_file=pdf_urls["fpe"],
                mca_file=pdf_urls["mca"],
                valueToSubmit=value,
            )
        case "first_encounter":
            # Handle first encounter logic
            return render_template(
                "registration.html",
                user=session.get("user"),
                fpe_file=pdf_urls["fpe"],
                mca_file=pdf_urls["mca"],
                valueToSubmit=value,
            )
        case "second_encounter":
            # Handle second encounter logic
            return render_template(
                "secondencounter.html",
                user=session.get("user"),
                ekass_epress=pdf_urls["ekass_epress"],
                valueToSubmit=value,
            )

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
        member = True if data["data"]["patientIsMember"] == "member" else False
        dependent = True if data["data"]["patientIsMember"] == "dependent" else False
        transfer = True if data["data"]["transfer"]["transfer"] == True else False

        initials = session.get("initials")

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
            "PreviousPCC": data['data']['transfer']['previousPCC'],
            "UserInitial": initials
        }

        pcsf_data = {
            key: value.upper() if isinstance(value, str) else value
            for key, value in pcsf_data.items()
        }

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
                    print(f"Processing field: {widget.field_name}, Type: {widget.field_type}, Value: {value}")   
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
        del doc          # Delete the variable
        gc.collect()

        print("PDF filled and flattened successfully.")
        # --- PYPDF WRITE START ---
        # Apply data to fields

        # Make sure output directory exists
        os.makedirs(os.path.dirname(output_pdf), exist_ok=True)

        # Save data to output path
        # with open(output_pdf, "wb") as output_file:
        #     writer.write(output_file)

        attach_images_to_pdf(output_pdf, 
                             data, 
                             UPLOAD_FOLDER, 
                             user_id,
                             FRONT_X,
                             FRONT_Y,
                             BACK_X,
                             BACK_Y,
                             BIRTH_CERT_X,
                             BIRTH_CERT_Y,
                             MAX_WIDTH,
                             BIRTH_CERT_MAX_WIDTH,
                             BIRTH_CERT_MAX_HEIGHT,
                             rotation_birth=-90,
                             rotation_id=0)
        fill_MCA(data)
        fill_PKRF_CHS(data)


    except Exception as e:
        # return jsonify({"status": "error", "message": str(e)}), 500
        print(f"This is the error{e}")
        traceback.print_exc()
    
    pdf_urls = get_current_user_pdf_urls(session.get("user_id"))

    if data['valueToSubmit'] == "registration":
        try:
            conn = get_db_connection()

            cursor = conn.cursor(pymysql.cursors.DictCursor)

            pdf_url = url_for(
                'static',
                filename=f"pdfs/user_{user_id}/output/PCSF_OUTPUT_user_{user_id}{check_form_version(session.get('feature_enabled', False))}.pdf"
            )


            mem_dep = (
                "Member"
                if pcsf_data['Member'] == True
                else "Dependent"
                if pcsf_data["Dependent"] == True
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
                        proccess_by,
                        DateTimeProccess
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    pcsf_data["LastName"],
                    pcsf_data["FirstName"],
                    pcsf_data["MiddleName"],
                    pcsf_data["Barangay"],
                    pcsf_data["PIN"],
                    mem_dep,
                    pcu_transaction,
                    user_id,
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
                        proccess_by,
                        DateTimeProccess
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    pcsf_data["LastName"],
                    pcsf_data["FirstName"],
                    pcsf_data["MiddleName"],
                    pcsf_data["Barangay"],
                    pcsf_data["PIN"],
                    mem_dep,
                    pcu_transaction,
                    user_id,
                    datetime.now()
                ))

            conn.commit()
                        
            return jsonify({
                "success": True,
                "message": "Record inserted successfully",
                "inserted_id": cursor.lastrowid,
                "pdf_url": {"pcsf": pdf_urls["pcsf"], "fpe": pdf_urls["fpe"], "mca_pdf": pdf_urls["mca"]}
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
    
    return jsonify({
                "success": True,
                "message": "Record inserted successfully",
                "pdf_url": {"fpe": pdf_urls["fpe"], "mca_pdf": pdf_urls["mca"]}
            }), 200

@app.route("/delete/<int:id>", methods=["DELETE"])
def delete_record(id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM cec_registration WHERE id = %s", (id,))
    conn.commit()

    return jsonify({
        "status": "success",
        "message": "Record deleted successfully."
    })

@app.route("/deleteTransfer/<int:id>", methods=["DELETE"])
def delete_transfer_record(id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM cec_transfer WHERE id = %s", (id,))
    conn.commit()

    return jsonify({
        "status": "success",
        "message": "Transfer record deleted successfully."
    })

@app.route("/Update/<int:id>", methods=["PUT"])
def update_record(id):
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE cec_registration
        SET LastName=%s, FirstName=%s, MiddleName=%s, Barangay=%s, PIN=%s, MemDep=%s, PCUTransaction=%s
        WHERE id=%s
    """, (
        data['LastName'],
        data['FirstName'],
        data['MiddleName'],
        data['Barangay'],
        data['PIN'],
        data['MemDep'],
        data['PCUTransaction'],
        id
    ))

    conn.commit()

    return jsonify({
        "status": "success",
        "message": "Record updated successfully."
    })

@app.route("/UpdateTransfer/<int:id>", methods=["PUT"])
def update_transfer_record(id):
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE cec_transfer
        SET LastName=%s, FirstName=%s, MiddleName=%s, Barangay=%s, PIN=%s, MemDep=%s, PCUTransaction=%s
        WHERE id=%s
    """, (
        data['LastName'],
        data['FirstName'],
        data['MiddleName'],
        data['Barangay'],
        data['PIN'],
        data['MemDep'],
        data['PCUTransaction'],
        id
    ))

    conn.commit()

    return jsonify({
        "status": "success",
        "message": "Record updated successfully."
    })

@app.route("/registrationToTransfer/<int:id>", methods=["POST"])
def registration_to_transfer(id):
    conn = get_db_connection()

    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM cec_registration WHERE id = %s", (id,))

    existing = cursor.fetchone()

    print(existing)

    cursor.execute("""
        INSERT INTO cec_transfer (LastName, FirstName, MiddleName, Barangay, PIN, MemDep, PCUTransaction)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        existing['LastName'],
        existing['FirstName'],
        existing['MiddleName'],
        existing['Barangay'],
        existing['PIN'],
        existing['MemDep'],
        existing['PCUTransaction']
    ))

    cursor.execute("DELETE FROM cec_registration WHERE id = %s", (id,))

    conn.commit()

    return jsonify({
        "status": "success",
        "message": "Record transferred successfully."
    })

@app.route("/transferToRegistration/<int:id>", methods=["POST"])
def transfer_to_registration(id):
    conn = get_db_connection()
    
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM cec_transfer WHERE id = %s", (id,))

    existing = cursor.fetchone()
    print(id)

    cursor.execute("""
        INSERT INTO cec_registration (LastName, FirstName, MiddleName, Barangay, PIN, MemDep, PCUTransaction)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        existing['LastName'],
        existing['FirstName'],
        existing['MiddleName'],
        existing['Barangay'],
        existing['PIN'],
        existing['MemDep'],
        existing['PCUTransaction']
    ))

    cursor.execute("DELETE FROM cec_transfer WHERE id = %s", (id,))

    conn.commit()

    return jsonify({
        "status": "success",
        "message": "Record transferred successfully."
    })

@app.route("/scanner")
def scannerPage():
    return render_template("scanner.html")

@app.route("/users")
def usersPage():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            firstName,
            lastName,
            username,
            password,
            status
        FROM users
        ORDER BY id DESC
    """)

    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("users.html", users=users)


@app.route('/users/update-status', methods=['POST'])
def update_user_status():

    try:
        user_id = request.form.get('user_id')
        status = request.form.get('status')

        if not user_id or status not in ['0', '1']:
            return jsonify({
                'success': False,
                'message': 'Invalid user ID or status.'
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users
            SET status = %s
            WHERE id = %s
        """, (int(status), int(user_id)))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'User status updated successfully.',
            'status': int(status)
        })

    except Exception as e:

        print("Update status error:", e)

        return jsonify({
            'success': False,
            'message': 'Failed to update user status.'
        }), 500


# ---------------------------------------------------------
# Edit User
# ---------------------------------------------------------

@app.route('/users/update', methods=['POST'])
def update_user():
    try:
        user_id = request.form.get('user_id')
        first_name = request.form.get('firstName', '').strip()
        last_name = request.form.get('lastName', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID is required.'
            }), 400

        if not first_name or not last_name or not username:
            return jsonify({
                'success': False,
                'message': 'First name, last name and username are required.'
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # If password is empty, don't change the existing password
        if password:

            cursor.execute("""
                UPDATE users
                SET firstName = %s,
                    lastName = %s,
                    username = %s,
                    password = %s
                WHERE id = %s
            """, (
                first_name,
                last_name,
                username,
                password,
                int(user_id)
            ))

        else:

            cursor.execute("""
                UPDATE users
                SET firstName = %s,
                    lastName = %s,
                    username = %s
                WHERE id = %s
            """, (
                first_name,
                last_name,
                username,
                int(user_id)
            ))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'User updated successfully.'
        })

   
    except Exception as e:

        print("Update user error:", e)

        return jsonify({
            'success': False,
            'message': 'Failed to update user.'
        }), 500


# ---------------------------------------------------------
# Delete User
# ---------------------------------------------------------

@app.route('/users/delete', methods=['POST'])
def delete_user():

    try:

        user_id = request.form.get('user_id')

        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID is required.'
            }), 400

        # Make sure user_id is an integer
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid user ID.'
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # -------------------------------------------------
        # Check if user exists
        # -------------------------------------------------

        cursor.execute("""
            SELECT id
            FROM users
            WHERE id = %s
        """, (user_id,))

        user = cursor.fetchone()

        if not user:

            cursor.close()
            conn.close()

            return jsonify({
                'success': False,
                'message': 'User not found.'
            }), 404

        # -------------------------------------------------
        # Delete user from database
        # -------------------------------------------------

        cursor.execute("""
            DELETE FROM users
            WHERE id = %s
        """, (user_id,))

        conn.commit()

        cursor.close()
        conn.close()

        # -------------------------------------------------
        # Delete user's PDF folder
        # -------------------------------------------------

        user_folder = os.path.join(
            app.root_path,
            'static',
            'pdfs',
            f'user_{user_id}'
        )

        if os.path.exists(user_folder):

            if os.path.isdir(user_folder):

                shutil.rmtree(user_folder)

                print(
                    f"Deleted user folder: {user_folder}"
                )

        # -------------------------------------------------
        # Success
        # -------------------------------------------------

        return jsonify({
            'success': True,
            'message': 'User and user PDF folder deleted successfully.'
        })

    except Exception as e:

        print("Delete user error:", e)

        return jsonify({
            'success': False,
            'message': 'Failed to delete user.'
        }), 500

if __name__ == '__main__':
    if serve is not None:
        serve(app, host="0.0.0.0", port=8180)
    else:
        app.run(host="0.0.0.0", port=5000, debug=True)
