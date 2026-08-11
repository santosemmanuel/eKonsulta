import json
import os
import io
import gc
from datetime import datetime
from zoneinfo import ZoneInfo
from pypdf import PdfReader, PdfWriter
from reportlab.lib.utils import ImageReader
import fitz
from flask import current_app, session, jsonify, url_for
from reportlab.pdfgen import canvas
from fillpdf import fillpdfs
from utils.helper import (
    check_form_version,
    get_age_display,
    generate_qr_code,
    add_qr_to_pdf,
    get_auto_fontsize,
    process_image,
    decode_image_data_url,
    create_pdf_image_overlay,
    attach_images_to_pdf
)

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
    user_id = session.get("user_id")

    FRONT_X = 10
    FRONT_Y = 10

    BIRTH_CERT_X = 10
    BIRTH_CERT_Y = 10

    BACK_X = 200
    BACK_Y = 10

    BIRTH_CERT_MAX_WIDTH = 450
    BIRTH_CERT_MAX_HEIGHT = 660
    MAX_WIDTH = 280

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
        
        UPLOAD_FOLDER = os.path.join(
        current_app.root_path, f"static/pdfs/user_{user_id}/uploads")

        pcu = "PCU Verification Failed"
        if data['data']['transactionInfo']['transactionNumber'] != '' :
            pcu = f"PCU Transaction Number: {data['data']['transactionInfo']['transactionNumber']}"

        date_object = datetime.strptime(data['data']['otherDetails']['dob'], "%Y-%m-%d")
        formatted_date = date_object.strftime('%m-%d-%Y')
        initials = session.get('initials')
        age = get_age_display(data["data"]["otherDetails"]["dob"])

        gender = data["data"]["otherDetails"]['sex']
        patientMiddleName = (
            data["data"]["personalInfo"]["middleName"][0] if data["data"]["personalInfo"]["middleName"] else ""
        )
        patientFullName = f"{data["data"]['personalInfo']['firstName']} {patientMiddleName} {data["data"]['personalInfo']['lastName']} {data["data"]['personalInfo']['nameExt']}"

        member = "Yes" if data["data"]["patientIsMember"] == "member" else ""
        dependent = "Yes" if data["data"]["patientIsMember"] == "dependent" else ""
        barangay = data["data"]["address"]["barangay"]
        representative = data["data"]["otherDetails"].get("representative", "") or ""
        reprelation = ""
        if data["data"]["otherDetails"]["relationship"] == "Others":
            reprelation = data["data"]["otherDetails"]["otherRelationship"]
        elif data["data"]["otherDetails"]["relationship"] != "-Select-":
            reprelation = data["data"]["otherDetails"]["relationship"]

        pin = data["data"]["pin"]
        if data["data"]["patientIsMember"] == "dependent":
            pin = data["data"]["dependentPin"]

        doc = fitz.open(pdf_path)

        chs_data = {
            "DateToday": f"{TODAY.month:02}/{TODAY.day:02}/{TODAY.year}",
            "LastName": data["data"]["personalInfo"]["lastName"],
            "FirstName": data["data"]["personalInfo"]["firstName"],
            "MiddleName": data["data"]["personalInfo"]["middleName"],
            "Barangay": barangay.upper(),
            "DOB": formatted_date,
            "PatientFullName": patientFullName,
            "FullAddress": f"{barangay.upper()}, {data['data']['address']['municipality']}, LEYTE",
            "MemberPIN": data["data"]["pin"] or "",
            "DependentPIN": data["data"]["dependentPin"],
            "NameExt": data["data"]["personalInfo"]["nameExt"] or "",
            "Age": age,
            "Gender": gender,
            "Representative": representative,
            "RepRelation": reprelation,
            "UserInitial": initials,
            "PatientSignOverPrinted": patientFullName,
            "PCU": pcu
        }

        chs_data = {
            key: value.upper() if isinstance(value, str) else value
            for key, value in chs_data.items()
        }

        for i, page in enumerate(doc):
            print(
                "Page:", i + 1,
                "Rotation:", page.rotation,
                "Rect:", page.rect
            )

        for page in doc:
            widgets = page.widgets()
        
        if widgets:
            for widget in widgets:
                field_name = widget.field_name

                if field_name in chs_data:
                    widget.field_value = chs_data[field_name]
                    widget.update()
            
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
                        font_size = 50.0  # Your preferred maximum starting font size
                        min_size = 12.0

                        # Auto-size logic: Reduce font size until the signature fits within the box width
                        while font_size >= min_size:
                            text_width = fitz.get_text_length(
                                str(value), fontname=font_name, fontsize=font_size)
                            if text_width <= rect.width:
                                break
                            font_size -= 0.5

                        # Center the signature text horizontally and vertically inside the box
                        font_size = get_auto_fontsize(value, rect)

                        down_offset = 12   # Increase to move DOWN
                        left_offset = 10    # Increase to move LEFT

                        x = rect.x0 + down_offset
                        y = rect.y1 - left_offset

                        page.insert_text(
                            (x, y),
                            str(value),
                            fontsize=font_size,
                            fontname=font_name,
                            rotate = 90
                        )

                # 3. Handle Fallback for All Other Text Fields (Left-aligned)
                else:
                    #if value:
                        # Vertically centers the text row within your fallback box height
                        # font_size = get_auto_fontsize(value, rect)
                        # adjusted_y = rect.y1 - \
                        #     ((rect.height - font_size) / 2.0) - \
                        #     (font_size * 0.05)

                        # page.insert_text(
                        #     (rect.x0 + 10, adjusted_y - 20),
                        #     str(value),
                        #     fontsize=font_size,
                        #     rotate = -270
                        # )
                    if value:
                        font_size = get_auto_fontsize(value, rect)

                        down_offset = 12   # Increase to move DOWN
                        left_offset = 10    # Increase to move LEFT

                        x = rect.x0 + down_offset
                        y = rect.y1 - left_offset

                        page.insert_text(
                            (x, y),
                            str(value),
                            fontsize=font_size,
                            fontname="helv",
                            rotate=90
                        )
            
                # Remove interactive form field element from the page layout canvas
                page.delete_widget(widget)
            doc.save(output_pdf)
            doc.close()
            del doc          # Delete the variable
            gc.collect()

            attach_images_to_pdf(
                output_pdf=output_pdf,
                data=data,
                upload_folder=UPLOAD_FOLDER,
                user_id=user_id,

                front_x=FRONT_X,
                front_y=FRONT_Y,

                back_x=BACK_X,
                back_y=BACK_Y,

                birth_x=BIRTH_CERT_X,
                birth_y=BIRTH_CERT_Y,

                max_width=MAX_WIDTH,
                birth_max_width=BIRTH_CERT_MAX_WIDTH,
                birth_max_height=BIRTH_CERT_MAX_HEIGHT,

                rotation_birth=0,
                rotation_id=90
            )
    except Exception as e:
        print(f"fill_PKRF_CHS error: {e}")


def fill_MCA(data):
    user_id = session.get("user_id")

    FRONT_X = 3020
    FRONT_Y = 2690

    BIRTH_CERT_X = 430
    BIRTH_CERT_Y = 100

    BACK_X = 420
    BACK_Y = 200

    BIRTH_CERT_MAX_WIDTH = 490
    BIRTH_CERT_MAX_HEIGHT = 700
    MAX_WIDTH = 980
    
    try:
        philhealth = "✔" if data['data']['transactionInfo']['philhealth'] == True else "✘"
        philsys = "✔" if data['data']['transactionInfo']['philsys'] == True else "✘"
        pcu = "PCU Verification Failed"
        if data['data']['transactionInfo']['transactionNumber'] != '' :
            pcu = f"PCU Transaction Number: {data['data']['transactionInfo']['transactionNumber']} \t\t PhilHealth: {philhealth} \t PhilSys: {philsys}"

        pdf_path = os.path.join(
            current_app.root_path,
            f"static/pdfs/user_{session.get('user_id')}/template/EMPANELMENT_(MCA)_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf"
        )
        output_pdf = os.path.join(
            current_app.root_path,
            f"static/pdfs/user_{session.get('user_id')}/output/EMPANELMENT_(MCA)_OUTPUT_user_{session.get('user_id')}{check_form_version(session.get('feature_enabled', False))}.pdf"
        )
        form_fields = list(fillpdfs.get_form_fields(pdf_path).keys())

        UPLOAD_FOLDER = os.path.join(
        current_app.root_path, f"static/pdfs/user_{user_id}/uploads")

        initials = session.get("initials")

        pin = data['data']['pin']
        if data['data']['patientIsMember'] == 'dependent':
            pin = data['data']['dependentPin']

        date_object = datetime.strptime(data['data']["otherDetails"]["dob"], "%Y-%m-%d")
        formatted_date = date_object.strftime('%m-%d-%Y')
        cellphoneNum = data['data']["otherDetails"]["mobile"]
        patientMiddleName = (
            data['data']["personalInfo"]["middleName"][0] if data['data']["personalInfo"]["middleName"] else ""
        )
        patientFullName = f"{data['data']['personalInfo']['firstName']} {patientMiddleName} {data['data']['personalInfo']['lastName']} {data['data']['personalInfo']['nameExt']}"

        member = "Yes" if data['data']["patientIsMember"] == "member" else None
        dependent = "Yes" if data['data']["patientIsMember"] == "dependent" else None
        representative = data['data']["otherDetails"].get("representative", "") or ""
        reprelation = ""
        if data['data']["otherDetails"]["relationship"] == "Others":
            reprelation = data['data']["otherDetails"]["otherRelationship"]
        elif data['data']["otherDetails"]["relationship"] != "-Select-":
            reprelation = data['data']["otherDetails"]["relationship"]
        
        doc = fitz.open(pdf_path)

        mca_data = {
            "PatientName": patientFullName,
            "DOB": formatted_date,
            "PIN": pin,
            "FullnameAndDateBeneficiary": f"{patientFullName}\t\t {TODAY.month:02}/{TODAY.day:02}/{TODAY.year}",
            "Representative": representative,
            "RepRelation": reprelation,
            "PCU": pcu,
            "UserInitial": initials,
            "PatientSignOverPrinted": patientFullName
        }

        mca_data = {
            key: value.upper() if isinstance(value, str) else value
            for key, value in mca_data.items()
        }
    
        for page in doc:
            widgets = page.widgets()

        if widgets:
            for widget in widgets:
                field_name = widget.field_name

                if field_name in mca_data:
                    widget.field_value = mca_data[field_name]
                    widget.update()

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
                            min_size = 12.0

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

            attach_images_to_pdf(
                output_pdf=output_pdf,
                data=data,
                upload_folder=UPLOAD_FOLDER,
                user_id=user_id,

                front_x=FRONT_X,
                front_y=FRONT_Y,

                back_x=BACK_X,
                back_y=BACK_Y,

                birth_x=BIRTH_CERT_X,
                birth_y=BIRTH_CERT_Y,

                max_width=MAX_WIDTH,
                birth_max_width=BIRTH_CERT_MAX_WIDTH,
                birth_max_height=BIRTH_CERT_MAX_HEIGHT,

                rotation_birth=-90,
                rotation_id=0
            )

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
