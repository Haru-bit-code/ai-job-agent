# ─────────────────────────────────────────────
# PURPOSE: Extract raw text from a PDF resume
# ─────────────────────────────────────────────

import fitz  # this is PyMuPDF (confusingly named fitz)
import os

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Takes a path to a PDF file.
    Returns all the text inside it as one big string.
    """

    # Safety check — does the file actually exist?
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found at: {pdf_path}")

    # Open the PDF
    # fitz.open() loads the entire PDF into memory
    document = fitz.open(pdf_path)

    all_text = []  # we'll collect text page by page

    # Loop through every page
    # document has a length — number of pages
    for page_number in range(len(document)):

        # Get the page object
        page = document[page_number]

        # Extract text from this page
        # get_text() returns a raw string of everything on the page
        page_text = page.get_text()

        all_text.append(page_text)

    # Close the document (good practice — frees memory)
    document.close()

    # Join all pages with a newline between them
    full_text = "\n".join(all_text)

    # Remove excessive blank lines (common in PDFs)
    # This splits on newlines, filters empty lines, rejoins
    cleaned_lines = [line.strip() for line in full_text.split("\n") if line.strip()]
    cleaned_text = "\n".join(cleaned_lines)

    return cleaned_text


# ─────────────────────────────────────────────
# TEST: Run this file directly to verify it works
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # Put your resume PDF in the data/ folder
    text = extract_text_from_pdf("data/resume.pdf")

    print("=== EXTRACTED TEXT (first 500 chars) ===")
    print(text[:500])
    print(f"\n=== TOTAL LENGTH: {len(text)} characters ===")