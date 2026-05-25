def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    import PyPDF2

    text = ""
    with open(file_path, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text


def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def extract_text_from_sql(file_path: str) -> str:
    """Extract text from SQL file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def extract_text_from_log(file_path: str) -> str:
    """Extract text from LOG file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file."""
    import docx

    text = ""
    doc = docx.Document(file_path)
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text


def extract_text(file_path: str, document_type: str) -> str:
    """Extract text based on document type."""
    extractors = {
        "pdf": extract_text_from_pdf,
        "txt": extract_text_from_txt,
        "sql": extract_text_from_sql,
        "log": extract_text_from_log,
        "docx": extract_text_from_docx,
    }
    
    extractor = extractors.get(document_type.lower())
    if not extractor:
        raise ValueError(f"Unsupported document type: {document_type}")
    
    return extractor(file_path)
