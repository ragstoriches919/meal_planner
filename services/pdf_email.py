from __future__ import annotations

import os
import re
import smtplib
import tempfile
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from fpdf import FPDF

load_dotenv()

_EMAIL = os.getenv("EMAIL", "")
_SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

_STRIP_MD = re.compile(r"\*\*(.+?)\*\*|\*(.+?)\*|__(.+?)__|_(.+?)_|`(.+?)`")

_UNICODE_MAP = {
    "–": "-", "—": "--", "‘": "'", "’": "'",
    "“": '"', "”": '"', "…": "...", "°": " deg",
    "½": "1/2", "¼": "1/4", "¾": "3/4",
    "™": "(TM)", "®": "(R)", "©": "(C)",
    "•": "-", "×": "x", "÷": "/",
}


def _clean(text: str) -> str:
    """Strip inline markdown markers and sanitize to Latin-1 safe text."""
    text = _STRIP_MD.sub(lambda m: next(g for g in m.groups() if g is not None), text)
    for char, replacement in _UNICODE_MAP.items():
        text = text.replace(char, replacement)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _build_pdf(name: str, recipe_markdown: str) -> bytes:
    pdf = FPDF()
    pdf.set_margins(20, 20, 20)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(20, 20, 20)
    pdf.multi_cell(0, 11, name, align="C")
    pdf.ln(4)

    # Divider
    pdf.set_draw_color(180, 180, 180)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(8)

    for raw_line in recipe_markdown.splitlines():
        line = raw_line.rstrip()

        # Section headers
        if line.startswith("### "):
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(60, 60, 60)
            pdf.ln(3)
            pdf.multi_cell(0, 7, _clean(line[4:]))
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(50, 50, 50)
            continue

        if line.startswith("## "):
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(30, 30, 30)
            pdf.ln(5)
            pdf.multi_cell(0, 8, _clean(line[3:]))
            pdf.ln(2)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(50, 50, 50)
            continue

        if line.startswith("# "):
            pdf.set_font("Helvetica", "B", 15)
            pdf.set_text_color(20, 20, 20)
            pdf.ln(5)
            pdf.multi_cell(0, 9, _clean(line[2:]))
            pdf.ln(3)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(50, 50, 50)
            continue

        # Blank line
        if not line.strip():
            pdf.ln(3)
            continue

        # Bullet points
        stripped = line.strip()
        if stripped.startswith(("- ", "* ", "• ")):
            text = _clean(stripped[2:].strip())
            x_before = pdf.get_x()
            pdf.set_x(26)
            pdf.cell(5, 6, "\x95")  # bullet char
            pdf.multi_cell(0, 6, text)
            continue

        # Numbered list items  (1. / 2. etc.)
        num_match = re.match(r"^(\d+\.\s+)(.*)", stripped)
        if num_match:
            label, text = num_match.group(1), _clean(num_match.group(2))
            pdf.set_x(24)
            pdf.cell(8, 6, label)
            pdf.multi_cell(0, 6, text)
            continue

        # Regular paragraph text
        pdf.multi_cell(0, 6, _clean(stripped))

    return bytes(pdf.output())


def send_recipe_email(name: str, recipe_markdown: str) -> None:
    if not _EMAIL:
        raise ValueError("EMAIL is not set in .env")
    if not _SMTP_PASSWORD:
        raise ValueError("SMTP_PASSWORD is not set in .env")

    pdf_bytes = _build_pdf(name, recipe_markdown)

    msg = MIMEMultipart()
    msg["From"] = _EMAIL
    msg["To"] = _EMAIL
    msg["Subject"] = f"Recipe: {name}"
    msg.attach(MIMEText(f"Here's your recipe for {name}!\n\nEnjoy your meal.", "plain"))

    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(pdf_bytes)
    encoders.encode_base64(attachment)
    safe_name = re.sub(r"[^\w\s-]", "", name).strip().replace(" ", "_")
    attachment.add_header("Content-Disposition", f'attachment; filename="{safe_name}.pdf"')
    msg.attach(attachment)

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(_EMAIL, _SMTP_PASSWORD)
        smtp.sendmail(_EMAIL, _EMAIL, msg.as_string())
