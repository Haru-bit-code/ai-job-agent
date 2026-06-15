# ─────────────────────────────────────────────────────
# PURPOSE: Split resume text into meaningful sections
# ─────────────────────────────────────────────────────

import re

RESUME_SECTIONS = [
    "PROFESSIONAL SUMMARY",
    "SUMMARY",
    "TECHNICAL SKILLS",
    "SKILLS",
    "PROJECTS",
    "WORK EXPERIENCE",
    "EDUCATION",
    "CERTIFICATIONS",
    "ACHIEVEMENTS",
]

def find_sections(text: str) -> list[dict]:
    """
    Finds section headers by looking for lines where
    the ENTIRE line matches a known section name.
    
    This prevents matching "experience" inside a sentence.
    """
    section_positions = []
    
    # Split text into lines and track character positions
    current_pos = 0
    
    for line in text.split("\n"):
        stripped = line.strip().upper()  # normalize to uppercase
        
        # Check if this entire line IS a section header
        # (not just contains one)
        for section_name in RESUME_SECTIONS:
            if stripped == section_name:
                section_positions.append({
                    "section": section_name,
                    "start": current_pos
                })
                break  # one match per line is enough
        
        # Move position forward (line length + 1 for the newline)
        current_pos += len(line) + 1
    
    return section_positions


def chunk_resume(text: str) -> list[dict]:
    """
    Takes full resume text.
    Returns list of section chunks as dictionaries.
    """
    chunks = []
    
    # Find all section positions using line-based matching
    section_positions = find_sections(text)
    
    if not section_positions:
        # Fallback: if no sections found, return whole text as one chunk
        print("⚠️  Warning: No section headers detected.")
        print("   Check if your resume uses standard section names.")
        return [{
            "chunk_id": "chunk_0",
            "section": "FULL_RESUME",
            "content": text.strip()
        }]
    
    # Sort by position (safety measure)
    section_positions.sort(key=lambda x: x["start"])
    
    # Extract content between sections
    for i, section in enumerate(section_positions):
        start = section["start"]
        
        if i + 1 < len(section_positions):
            end = section_positions[i + 1]["start"]
        else:
            end = len(text)
        
        content = text[start:end].strip()
        
        if len(content) < 20:
            continue
        
        chunks.append({
            "chunk_id": f"chunk_{i}",
            "section": section["section"],
            "content": content
        })
    
    # Add header chunk (everything before first section)
    first_start = section_positions[0]["start"]
    header = text[:first_start].strip()
    
    if header:
        chunks.insert(0, {
            "chunk_id": "chunk_header",
            "section": "HEADER",
            "content": header
        })
    
    return chunks


# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":
    from extract import extract_text_from_pdf

    text = extract_text_from_pdf("data/resume.pdf")
    chunks = chunk_resume(text)

    print(f"=== TOTAL CHUNKS FOUND: {len(chunks)} ===\n")

    for chunk in chunks:
        print(f"── SECTION: {chunk['section']} ──")
        print(f"   ID: {chunk['chunk_id']}")
        print(f"   LENGTH: {len(chunk['content'])} chars")
        print(f"   PREVIEW: {chunk['content'][:120]}...")
        print()