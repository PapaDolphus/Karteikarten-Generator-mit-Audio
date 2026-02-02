"""
PDF Parser für Karteikarten-Generator

Extrahiert Text aus PDF-Dateien und identifiziert unterstrichene Überschriften
als Strukturelemente für die Karteikarten-Generierung.
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List, Tuple
import re


def extract_sections_from_pdf(pdf_path: str) -> Dict[str, str]:
    """
    Extrahiert Abschnitte aus einer PDF-Datei.
    
    Identifiziert unterstrichene Text-Elemente als Überschriften und
    gruppiert den nachfolgenden Text als Abschnittsinhalt.
    
    Args:
        pdf_path: Pfad zur PDF-Datei
        
    Returns:
        Dictionary mit Überschriften als Keys und Abschnittsinhalten als Values
    """
    doc = fitz.open(pdf_path)
    sections = {}
    
    all_content = []
    underlined_positions = []
    
    for page_num, page in enumerate(doc):
        # Text mit Position extrahieren
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if "lines" not in block:
                continue
                
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue
                    
                    # Prüfen ob Text unterstrichen ist
                    # PyMuPDF: flags & 2^0 = superscript, 2^1 = italic, 2^2 = serifed, 
                    # 2^3 = monospaced, 2^4 = bold
                    # Unterstreichung wird über Annotationen oder Linien erkannt
                    flags = span.get("flags", 0)
                    bbox = span["bbox"]
                    
                    is_underlined = _check_underline(page, bbox)
                    
                    all_content.append({
                        "text": text,
                        "page": page_num,
                        "bbox": bbox,
                        "is_underlined": is_underlined,
                        "is_bold": bool(flags & 16),
                        "font_size": span.get("size", 12)
                    })
    
    doc.close()
    
    # Abschnitte basierend auf unterstrichenen Überschriften erstellen
    sections = _build_sections(all_content)
    
    return sections


def _check_underline(page, text_bbox: Tuple[float, float, float, float]) -> bool:
    """
    Prüft ob ein Textbereich unterstrichen ist.
    
    Sucht nach Linien-Annotationen oder Zeichnungen unter dem Text.
    
    Args:
        page: PyMuPDF Page-Objekt
        text_bbox: Bounding Box des Texts (x0, y0, x1, y1)
        
    Returns:
        True wenn unterstrichen, sonst False
    """
    x0, y0, x1, y1 = text_bbox
    
    # Toleranzbereich für Unterstreichung (unter dem Text)
    underline_zone_top = y1
    underline_zone_bottom = y1 + 5  # 5 Punkte unter dem Text
    
    # Prüfe Annotationen
    for annot in page.annots():
        if annot.type[0] == 8:  # Underline annotation
            annot_rect = annot.rect
            if (annot_rect.x0 <= x0 and annot_rect.x1 >= x1 and
                annot_rect.y0 <= y1 and annot_rect.y1 >= y0):
                return True
    
    # Prüfe gezeichnete Linien (drawings)
    drawings = page.get_drawings()
    for drawing in drawings:
        for item in drawing.get("items", []):
            if item[0] == "l":  # Linie
                line_start = item[1]
                line_end = item[2]
                
                # Horizontale Linie unter dem Text?
                if (abs(line_start.y - line_end.y) < 2 and  # Fast horizontal
                    underline_zone_top <= line_start.y <= underline_zone_bottom and
                    line_start.x <= x0 + 5 and line_end.x >= x1 - 5):
                    return True
    
    return False


def _build_sections(content_items: List[Dict]) -> Dict[str, str]:
    """
    Baut Abschnitte aus den extrahierten Content-Items.
    
    Args:
        content_items: Liste von Content-Dictionaries
        
    Returns:
        Dictionary mit Abschnitten
    """
    sections = {}
    current_heading = None
    current_content = []
    
    for item in content_items:
        # Neue Überschrift gefunden (unterstrichen oder deutlich größere/fette Schrift)
        if item["is_underlined"] or (item["is_bold"] and item["font_size"] > 12):
            # Vorherigen Abschnitt speichern
            if current_heading and current_content:
                sections[current_heading] = " ".join(current_content)
            
            current_heading = item["text"]
            current_content = []
        else:
            # Inhalt zum aktuellen Abschnitt hinzufügen
            current_content.append(item["text"])
    
    # Letzten Abschnitt speichern
    if current_heading and current_content:
        sections[current_heading] = " ".join(current_content)
    
    # Falls keine Überschriften gefunden wurden, gesamten Text als einen Abschnitt
    if not sections and content_items:
        full_text = " ".join([item["text"] for item in content_items])
        sections["Hauptinhalt"] = full_text
    
    return sections


def extract_text_only(pdf_path: str) -> str:
    """
    Extrahiert den gesamten Text aus einer PDF ohne Strukturierung.
    
    Args:
        pdf_path: Pfad zur PDF-Datei
        
    Returns:
        Gesamter Text als String
    """
    doc = fitz.open(pdf_path)
    text = ""
    
    for page in doc:
        text += page.get_text() + "\n\n"
    
    doc.close()
    return text.strip()


def chunk_text_into_sections(text: str, chunk_size: int = 4000, overlap: int = 200) -> Dict[str, str]:
    """
    Teilt einen langen Text in Chunks für die API-Verarbeitung.
    
    Versucht an Absatzgrenzen zu trennen, um semantische Zusammenhänge zu erhalten.
    
    Args:
        text: Der zu teilende Text
        chunk_size: Maximale Größe eines Chunks in Zeichen
        overlap: Überlappung zwischen Chunks für Kontext
        
    Returns:
        Dictionary mit Chunk-Namen als Keys und Chunk-Inhalten als Values
    """
    if len(text) <= chunk_size:
        return {"Gesamtinhalt": text}
    
    # Teile an Absätzen
    paragraphs = re.split(r'\n\s*\n', text)
    
    chunks = {}
    current_chunk = []
    current_length = 0
    chunk_num = 1
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # Wenn Absatz allein zu lang ist, teile ihn weiter
        if len(para) > chunk_size:
            # Speichere aktuellen Chunk falls vorhanden
            if current_chunk:
                chunks[f"Teil {chunk_num}"] = "\n\n".join(current_chunk)
                chunk_num += 1
                current_chunk = []
                current_length = 0
            
            # Teile langen Absatz an Sätzen
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sentence in sentences:
                if current_length + len(sentence) > chunk_size and current_chunk:
                    chunks[f"Teil {chunk_num}"] = "\n\n".join(current_chunk)
                    chunk_num += 1
                    # Behalte letzten Teil für Überlappung
                    if current_chunk:
                        overlap_text = current_chunk[-1][-overlap:] if len(current_chunk[-1]) > overlap else current_chunk[-1]
                        current_chunk = [overlap_text]
                        current_length = len(overlap_text)
                    else:
                        current_chunk = []
                        current_length = 0
                
                current_chunk.append(sentence)
                current_length += len(sentence)
        else:
            # Normaler Absatz
            if current_length + len(para) > chunk_size and current_chunk:
                chunks[f"Teil {chunk_num}"] = "\n\n".join(current_chunk)
                chunk_num += 1
                # Behalte letzten Absatz für Überlappung
                overlap_text = current_chunk[-1] if current_chunk else ""
                if len(overlap_text) > overlap:
                    overlap_text = overlap_text[-overlap:]
                current_chunk = [overlap_text] if overlap_text else []
                current_length = len(overlap_text) if overlap_text else 0
            
            current_chunk.append(para)
            current_length += len(para)
    
    # Letzten Chunk speichern
    if current_chunk:
        chunks[f"Teil {chunk_num}"] = "\n\n".join(current_chunk)
    
    return chunks


def extract_text_as_chunks(pdf_path: str, chunk_size: int = 4000) -> Dict[str, str]:
    """
    Extrahiert Text aus einer PDF und teilt ihn in Chunks.
    
    Args:
        pdf_path: Pfad zur PDF-Datei
        chunk_size: Maximale Größe eines Chunks in Zeichen
        
    Returns:
        Dictionary mit Chunk-Namen als Keys und Chunk-Inhalten als Values
    """
    text = extract_text_only(pdf_path)
    return chunk_text_into_sections(text, chunk_size)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Verwendung: python pdf_parser.py <pdf_datei>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    print(f"Extrahiere Abschnitte aus: {pdf_path}")
    
    sections = extract_sections_from_pdf(pdf_path)
    
    print(f"\n{len(sections)} Abschnitte gefunden:\n")
    for heading, content in sections.items():
        print(f"📌 {heading}")
        print(f"   {content[:200]}..." if len(content) > 200 else f"   {content}")
        print()
