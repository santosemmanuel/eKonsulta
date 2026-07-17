import base64
import io
import json
import tempfile
from datetime import datetime, date
from pypdf import PdfReader, PdfWriter
import cv2
import numpy as np
import fitz
import qrcode
import os
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


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

def get_auto_fontsize(text, rect, fontname="helv",
                      max_size=30, min_size=10, padding=2):
    """
    Returns the largest font size that fits within rect.width.
    """
    available_width = rect.width - (padding * 2)

    font_size = max_size

    while font_size >= min_size:
        text_width = fitz.get_text_length(
            str(text),
            fontname=fontname,
            fontsize=font_size
        )

        if text_width <= available_width:
            return font_size

        font_size -= 0.5

    return min_size


def decode_image_data_url(image_data):
    """Decode a base64 data URL or base64 string into raw bytes."""
    if not image_data:
        return None

    if isinstance(image_data, bytes):
        return image_data

    if isinstance(image_data, str):
        if image_data.startswith("data:"):
            parts = image_data.split(",", 1)
            if len(parts) == 2:
                image_data = parts[1]

        try:
            return base64.b64decode(image_data)
        except Exception:
            return None

    return None


def create_pdf_image_overlay(image_bytes, page_width, page_height,
                             x=None, y=None, max_width=250,
                             max_height=None, rotation=0):
    """Create a one-page PDF overlay containing a scaled image."""
    if not image_bytes:
        raise ValueError("Image bytes are required for overlay.")

    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_width, page_height))
    img = ImageReader(io.BytesIO(image_bytes))
    iw, ih = img.getSize()

    if max_height is None:
        max_height = page_height

    scale = min(max_width / iw, max_height / ih, 1.0)
    draw_w = iw * scale
    draw_h = ih * scale

    if x is None:
        x = page_width - draw_w - 20

    if y is None:
        y = (page_height - draw_h) / 2

    c.saveState()
    if rotation == -90:
        c.translate(x, y + draw_w)
    elif rotation == 90:
        c.translate(x + draw_h, y)
    elif rotation == 180:
        c.translate(x + draw_w, y + draw_h)
    else:
        c.translate(x, y)

    c.rotate(rotation)
    c.drawImage(img, 0, 0, width=draw_w, height=draw_h,    preserveAspectRatio=True,
    mask='auto')
    c.restoreState()
    c.save()

    packet.seek(0)
    return PdfReader(packet).pages[0]

def attach_images_to_pdf(
    output_pdf,
    data,
    upload_folder,
    user_id,
    front_x,
    front_y,
    back_x,
    back_y,
    birth_x,
    birth_y,
    max_width=280,
    birth_max_width=550,
    birth_max_height=550,
):
    """
    Attach Front/Back ID or Birth Certificate to an existing PDF.
    """

    front_image = data.get("front")
    back_image = data.get("back")
    birth_certificate = data.get("birthCertificate")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if birth_certificate:

        birth_filename = os.path.join(
            upload_folder,
            f"birth_certificate_{timestamp}.png"
        )

        birth_bytes = decode_image_data_url(birth_certificate)

        if not birth_bytes:
            raise Exception("Invalid birth certificate image.")

        processed_birth = process_image(birth_bytes)

        with open(birth_filename, "wb") as f:
            f.write(processed_birth)

        reader = PdfReader(output_pdf)
        writer = PdfWriter()

        page = reader.pages[0]

        pw = float(page.mediabox.width)
        ph = float(page.mediabox.height)

        overlay = create_pdf_image_overlay(
            processed_birth,
            pw,
            ph,
            x=birth_x,
            y=birth_y,
            max_width=birth_max_width,
            max_height=birth_max_height,
            rotation=-90,
        )

        page.merge_page(overlay)
        writer.add_page(page)

        for p in reader.pages[1:]:
            writer.add_page(p)

        temp_pdf = os.path.join(
            os.path.dirname(output_pdf),
            f"temp_birth_{timestamp}.pdf"
        )

        with open(temp_pdf, "wb") as f:
            writer.write(f)

        os.replace(temp_pdf, output_pdf)

        try:
            os.remove(birth_filename)
        except:
            pass

    else:

        front_filename = os.path.join(
            upload_folder,
            f"front_{timestamp}.png"
        )

        back_filename = os.path.join(
            upload_folder,
            f"back_{timestamp}.png"
        )

        front_bytes = decode_image_data_url(front_image)
        back_bytes = decode_image_data_url(back_image)

        if not front_bytes or not back_bytes:
            raise Exception("Invalid front/back image.")

        processed_front = front_bytes
        processed_back = back_bytes

        with open(front_filename, "wb") as f:
            f.write(processed_front)

        with open(back_filename, "wb") as f:
            f.write(processed_back)

        reader = PdfReader(output_pdf)
        writer = PdfWriter()

        page = reader.pages[0]

        pw = float(page.mediabox.width)
        ph = float(page.mediabox.height)

        overlay_front = create_pdf_image_overlay(
            processed_front,
            pw,
            ph,
            x=front_x,
            y=front_y,
            max_width=max_width,
        )

        overlay_back = create_pdf_image_overlay(
            processed_back,
            pw,
            ph,
            x=back_x,
            y=back_y,
            max_width=max_width,
        )

        page.merge_page(overlay_front)
        page.merge_page(overlay_back)

        writer.add_page(page)

        for p in reader.pages[1:]:
            writer.add_page(p)

        temp_pdf = os.path.join(
            os.path.dirname(output_pdf),
            f"temp_{timestamp}.pdf"
        )

        with open(temp_pdf, "wb") as f:
            writer.write(f)

        os.replace(temp_pdf, output_pdf)

        try:
            os.remove(front_filename)
            os.remove(back_filename)
        except:
            pass

