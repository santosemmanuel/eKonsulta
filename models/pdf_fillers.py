import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import current_app, session
from fillpdf import fillpdfs

from utils.helper import check_form_version, get_age_display, generate_qr_code, add_qr_to_pdf

TODAY = datetime.now(ZoneInfo("Asia/Manila")).date()


def fill_EKAS_EPRESS_MCA(data):
    philhealth = "✔" if data['transactionInfo']['philhealth'] == True else "✘"
    philsys = "✔" if data['transactionInfo']['philsys'] == True else "✘"
    pcu = "PCU Verification Failed"
    if data['transactionInfo']['transactionNumber'] != '':
        pcu = f"PCU Transaction Number: {data['transactionInfo']['transactionNumber']} \t\t PhilHealth: {philhealth} \t PhilSys: {philsys}"

    try:
        pdf_path = os.path.join(
            current_app.root_path,
            f"static/pdfs/user_{session.get('user_id')}/template/EKAS,EPRESS,MCA_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf"
        )
        output_pdf = os.path.join(
            current_app.root_path,
            f"static/pdfs/user_{session.get('user_id')}/output/EKAS,EPRESS,MCA_OUTPUT_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf"
        )
        form_fields = list(fillpdfs.get_form_fields(pdf_path).keys())

        initials = session.get("initials")
        pin = data['pin']
        memberDependent = "Member"
        if data['patientIsMember'] == 'dependent':
            memberDependent = "Dependent"
            pin = data['dependentPin']

        date_object = datetime.strptime(data["otherDetails"]["dob"], "%Y-%m-%d")
        formatted_date = date_object.strftime('%m-%d-%Y')
        age = get_age_display(data["otherDetails"]["dob"])
        cellphoneNum = data["otherDetails"]["mobile"]
        patientMiddleName = (
            data["personalInfo"]["middleName"][0] if data["personalInfo"]["middleName"] else ""
        )
        patientFullName = f"{data['personalInfo']['firstName']} {patientMiddleName} {data['personalInfo']['lastName']} {data['personalInfo']['nameExt']}"

        member = "Yes" if data["patientIsMember"] == "member" else None
        dependent = "Yes" if data["patientIsMember"] == "dependent" else None
        representative = data["otherDetails"].get("representative", "") or ""
        reprelation = ""
        if data["otherDetails"]["relationship"] == "Others":
            reprelation = data["otherDetails"]["otherRelationship"]
        elif data["otherDetails"]["relationship"] != "-Select-":
            reprelation = data["otherDetails"]["relationship"]

        data_map = {
            form_fields[form_fields.index("PatientName")]: patientFullName,
            form_fields[form_fields.index("DOB")]: formatted_date,
            form_fields[form_fields.index("PIN")]: pin,
            form_fields[form_fields.index("BenefitYear")]: TODAY.year,
            form_fields[form_fields.index("FullnameAndDateBeneficiary")]: f"{patientFullName}\t\t {TODAY.month:02}/{TODAY.day:02}/{TODAY.year}",
            form_fields[form_fields.index("Member")]: member,
            form_fields[form_fields.index("Dependent")]: dependent,
            form_fields[form_fields.index("Member1")]: member,
            form_fields[form_fields.index("Dependent2")]: dependent,
            form_fields[form_fields.index("ContactNum")]: cellphoneNum,
            form_fields[form_fields.index("Age")]: age,
            form_fields[form_fields.index("Performed")]: "Yes",
            form_fields[form_fields.index("DatePerformed")]: f"{TODAY.month:02}/{TODAY.day:02}/{TODAY.year}",
            form_fields[form_fields.index("Representative")]: representative,
            form_fields[form_fields.index("RepRelation")]: reprelation,
            form_fields[form_fields.index("PCU")]: pcu,
            form_fields[form_fields.index("UserInitial")]: initials,
        }

        patient_data_qr = {
            "pin": pin,
            "ln": data["personalInfo"]["lastName"],
            "fN": data['personalInfo']['firstName'],
            "mN": data["personalInfo"]["middleName"],
            "ext": data["personalInfo"]["nameExt"],
            "bod": data["otherDetails"]["dob"],
            "MD": memberDependent,
            "genDate": f"{TODAY.month:02}/{TODAY.day:02}/{TODAY.year}",
        }

        qr_patient = generate_qr_code(patient_data_qr)
        add_qr_to_pdf(pdf_path, output_pdf, qr_patient)
        fillpdfs.write_fillable_pdf(output_pdf, output_pdf, data_map, flatten=False)
    except Exception as e:
        print(f"fill_EKAS_EPRESS_MCA error: {e}")


def fill_PKRF_CHS(data):
    try:
        pdf_path = os.path.join(
            current_app.root_path,
            f"static/pdfs/user_{session.get('user_id')}/template/PKRF,Consent, Health Screening_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf"
        )
        output_pdf = os.path.join(
            current_app.root_path,
            f"static/pdfs/user_{session.get('user_id')}/output/PKRF,Consent, Health Screening_OUTPUT_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf"
        )
        form_fields = list(fillpdfs.get_form_fields(pdf_path).keys())

        date_object = datetime.strptime(data["otherDetails"]["dob"], "%Y-%m-%d")
        formatted_date = date_object.strftime('%m-%d-%Y')
        initials = session.get('initials')
        age = get_age_display(data["otherDetails"]["dob"])

        gender = data["otherDetails"]['sex']
        patientMiddleName = (
            data["personalInfo"]["middleName"][0] if data["personalInfo"]["middleName"] else ""
        )
        patientFullName = f"{data['personalInfo']['firstName']} {patientMiddleName} {data['personalInfo']['lastName']} {data['personalInfo']['nameExt']}"

        member = "Yes" if data["patientIsMember"] == "member" else ""
        dependent = "Yes" if data["patientIsMember"] == "dependent" else ""
        barangay = data["address"]["barangay"]
        representative = data["otherDetails"].get("representative", "") or ""
        reprelation = ""
        if data["otherDetails"]["relationship"] == "Others":
            reprelation = data["otherDetails"]["otherRelationship"]
        elif data["otherDetails"]["relationship"] != "-Select-":
            reprelation = data["otherDetails"]["relationship"]

        pin = data["pin"]
        if data["patientIsMember"] == "dependent":
            pin = data["dependentPin"]

        data_map = {
            form_fields[form_fields.index("Member")]: member,
            form_fields[form_fields.index("Dependent")]: dependent,
            form_fields[form_fields.index("PIN")]: pin,
            form_fields[form_fields.index("DateToday")]: f"{TODAY.month:02}/{TODAY.day:02}/{TODAY.year}",
            form_fields[form_fields.index("LastName")]: data["personalInfo"]["lastName"],
            form_fields[form_fields.index("FirstName")]: data["personalInfo"]["firstName"],
            form_fields[form_fields.index("MiddleName")]: data["personalInfo"]["middleName"],
            form_fields[form_fields.index("Barangay")]: barangay.upper(),
            form_fields[form_fields.index("Municipality")]: data["address"]["municipality"],
            form_fields[form_fields.index("Province")]: "LEYTE",
            form_fields[form_fields.index("DOB")]: formatted_date,
            form_fields[form_fields.index("ContactNum")]: data["otherDetails"]["mobile"],
            form_fields[form_fields.index("DepLastName")]: data["personalInfo"]["lastName"],
            form_fields[form_fields.index("DepFirstName")]: data["personalInfo"]["firstName"],
            form_fields[form_fields.index("DepMiddleName")]: data["personalInfo"]["middleName"],
            form_fields[form_fields.index("PatientSignature")]: patientFullName,
            form_fields[form_fields.index("PatientFullName")]: patientFullName,
            form_fields[form_fields.index("FullAddress")]: f"{barangay.upper()}, {data['address']['municipality']}, LEYTE",
            form_fields[form_fields.index("MemberPIN")]: data.get('pin', ''),
            form_fields[form_fields.index("DependentPIN")]: data.get('dependentPin', ''),
            form_fields[form_fields.index("NameExt")]: data["personalInfo"]["nameExt"],
            form_fields[form_fields.index("Age")]: age,
            form_fields[form_fields.index("Gender")]: gender,
            form_fields[form_fields.index("Representative")]: representative,
            form_fields[form_fields.index("RepRelation")]: reprelation,
            form_fields[form_fields.index("UserInitial")]: initials,
        }

        fillpdfs.write_fillable_pdf(pdf_path, output_pdf, data_map)
    except Exception as e:
        print(f"fill_PKRF_CHS error: {e}")


def fill_MCA(data):
    try:
        philhealth = "✔" if data['transactionInfo']['philhealth'] == True else "✘"
        philsys = "✔" if data['transactionInfo']['philsys'] == True else "✘"
        pcu = "PCU Verification Failed"
        if data['transactionInfo']['transactionNumber'] != '':
            pcu = f"PCU Transaction Number: {data['transactionInfo']['transactionNumber']} \t\t PhilHealth: {philhealth} \t PhilSys: {philsys}"

        pdf_path = os.path.join(
            current_app.root_path,
            f"static/pdfs/user_{session.get('user_id')}/template/EMPANELMENT_(MCA)_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf"
        )
        output_pdf = os.path.join(
            current_app.root_path,
            f"static/pdfs/user_{session.get('user_id')}/output/EMPANELMENT_(MCA)_OUTPUT_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf"
        )
        form_fields = list(fillpdfs.get_form_fields(pdf_path).keys())

        initials = session.get("initials")
        pin = data['pin']
        if data['patientIsMember'] == 'dependent':
            pin = data['dependentPin']

        date_object = datetime.strptime(data["otherDetails"]["dob"], "%Y-%m-%d")
        formatted_date = date_object.strftime('%m-%d-%Y')
        cellphoneNum = data["otherDetails"]["mobile"]
        patientMiddleName = (
            data["personalInfo"]["middleName"][0] if data["personalInfo"]["middleName"] else ""
        )
        patientFullName = f"{data['personalInfo']['firstName']} {patientMiddleName} {data['personalInfo']['lastName']} {data['personalInfo']['nameExt']}"

        member = "Yes" if data["patientIsMember"] == "member" else None
        dependent = "Yes" if data["patientIsMember"] == "dependent" else None
        representative = data["otherDetails"].get("representative", "") or ""
        reprelation = ""
        if data["otherDetails"]["relationship"] == "Others":
            reprelation = data["otherDetails"]["otherRelationship"]
        elif data["otherDetails"]["relationship"] != "-Select-":
            reprelation = data["otherDetails"]["relationship"]

        data_map = {
            form_fields[form_fields.index("PatientName")]: patientFullName,
            form_fields[form_fields.index("DOB")]: formatted_date,
            form_fields[form_fields.index("PIN")]: pin,
            form_fields[form_fields.index("BenefitYear")]: TODAY.year,
            form_fields[form_fields.index("FullnameAndDateBeneficiary")]: f"{patientFullName}\t\t {TODAY.month:02}/{TODAY.day:02}/{TODAY.year}",
            form_fields[form_fields.index("BenefitYear1")]: TODAY.year - 1,
            form_fields[form_fields.index("Representative")]: representative,
            form_fields[form_fields.index("RepRelation")]: reprelation,
            form_fields[form_fields.index("PCU")]: pcu,
            form_fields[form_fields.index("UserInitial")]: initials,
        }

        fillpdfs.write_fillable_pdf(pdf_path, output_pdf, data_map, flatten=False)
    except Exception as e:
        print(f"fill_MCA error: {e}")


def clean_files(file_list):
    for relative_path in file_list:
        try:
            file_path = os.path.join(current_app.root_path, "static", "pdfs", relative_path)
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted {relative_path}")
        except Exception as e:
            print(f"Error deleting {relative_path}: {e}")
