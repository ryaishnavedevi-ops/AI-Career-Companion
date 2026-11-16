
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

import pymupdf


def extract_pdf_text(file_path):
    with pymupdf.open(file_path) as document:
        text = "\n".join(
            page.get_text() for page in document
        )

    return text.strip()


def extract_docx_text(file_path):
    namespace = {
        "w": "http://schemas.openxmlformats.org/"
             "wordprocessingml/2006/main"
    }

    with ZipFile(file_path) as archive:
        xml_content = archive.read("word/document.xml")

    root = ET.fromstring(xml_content)
    paragraphs = []

    for paragraph in root.findall(".//w:p", namespace):
        text = "".join(
            node.text or ""
            for node in paragraph.findall(".//w:t", namespace)
        )

        if text.strip():
            paragraphs.append(text)

    return "\n".join(paragraphs)


def extract_resume_text(file_path):
    extension = Path(file_path).suffix.lower()

    if extension == ".pdf":
        return extract_pdf_text(file_path)

    elif extension == ".docx":
        return extract_docx_text(file_path)

    else:
        raise ValueError("Unsupported resume format")
