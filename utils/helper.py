import base64
import io
import json
import tempfile
from datetime import datetime, date

import cv2
import numpy as np
import fitz
import qrcode


def check_form_version(feature_enabled):
    return ".1" if feature_enabled else ""


def get_age_display(dob_string, format="%Y-%m-%d"):
    dob = datetime.strptime(dob_string, format).date()
    today = date.today()

    total_months = (today.year - dob.year) * 12 + (today.month - dob.month)
    if today.day < dob.day:
        total_months -= 1

    years = total_months // 12
    months = total_months % 12

    if years == 0 and months == 0:
        days = (today - dob).days
        return f"{days} day(s) old"
    elif years == 0:
        return f"{months} month(s)"
    else:
        return f"{years}"


def get_initials(full_name):
    words = full_name.split()
    initials = [word[0].upper() for word in words if word]
    return ".".join(initials)


def convert_to_sql_date(date_str):
    return datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m-%d")


def process_image(image_bytes, enhance=True):
    try:
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return image_bytes

        if enhance:
            img = cv2.bilateralFilter(img, 9, 75, 75)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            edged = cv2.Canny(blur, 50, 150)

            contours, _ = cv2.findContours(
                edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

            doc_cnt = None
            for c in contours:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.02 * peri, True)
                if len(approx) == 4:
                    doc_cnt = approx
                    break

            if doc_cnt is not None:
                pts = doc_cnt.reshape(4, 2)
                rect = np.zeros((4, 2), dtype="float32")

                s = pts.sum(axis=1)
                rect[0] = pts[np.argmin(s)]
                rect[2] = pts[np.argmax(s)]

                diff = np.diff(pts, axis=1)
                rect[1] = pts[np.argmin(diff)]
                rect[3] = pts[np.argmax(diff)]

                (tl, tr, br, bl) = rect
                widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
                widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
                maxWidth = max(int(widthA), int(widthB))

                heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
                heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
                maxHeight = max(int(heightA), int(heightB))

                dst = np.array([
                    [0, 0],
                    [maxWidth - 1, 0],
                    [maxWidth - 1, maxHeight - 1],
                    [0, maxHeight - 1]], dtype="float32")

                M = cv2.getPerspectiveTransform(rect, dst)
                warp = cv2.warpPerspective(img, M, (maxWidth, maxHeight))
                img = warp

            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            limg = cv2.merge((cl, a, b))
            img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        success, encoded = cv2.imencode('.png', img, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        return encoded.tobytes() if success else image_bytes
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
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        print(f"QR code generation error: {e}")
        return None


def add_qr_to_pdf(input_pdf, output_pdf, qr_image_bytes):
    try:
        doc = fitz.open(input_pdf)
        page = doc[0]

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(qr_image_bytes)
            qr_path = tmp.name

        rect = fitz.Rect(210, 15, 280, 85)
        page.insert_image(rect, filename=qr_path)
        doc.save(output_pdf)
        doc.close()
    except Exception as e:
        print(f"QR insertion error: {e}")
