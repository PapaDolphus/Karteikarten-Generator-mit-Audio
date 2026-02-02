"""
TSV Exporter für Karteikarten

Exportiert generierte Karteikarten im Tab-Separated-Values Format
für Import in Anki, Quizlet oder andere Lernkarten-Programme.
"""

import csv
from pathlib import Path
from typing import List, Dict


def export_to_tsv(flashcards: List[Dict[str, str]], output_path: str) -> int:
    """
    Exportiert Karteikarten in eine TSV-Datei.
    
    Format: Frage<TAB>Antwort
    
    Zeilenumbrüche in Antworten werden als HTML <br> oder escaped \\n beibehalten,
    da die meisten Lernkarten-Apps dies unterstützen.
    
    Args:
        flashcards: Liste von Dictionaries mit 'frage' und 'antwort' Keys
        output_path: Pfad zur Ausgabedatei
        
    Returns:
        Anzahl der exportierten Karteikarten
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    exported_count = 0
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
        
        for card in flashcards:
            frage = card.get('frage', '').strip()
            antwort = card.get('antwort', '').strip()
            
            if not frage or not antwort:
                continue
            
            # Zeilenumbrüche für Anki-Kompatibilität in HTML konvertieren
            # Anki versteht <br> Tags
            antwort_formatted = antwort.replace('\n', '<br>')
            
            writer.writerow([frage, antwort_formatted])
            exported_count += 1
    
    return exported_count


def export_to_tsv_plain(flashcards: List[Dict[str, str]], output_path: str) -> int:
    """
    Exportiert Karteikarten in eine TSV-Datei ohne HTML-Formatierung.
    
    Zeilenumbrüche werden als escaped \\n beibehalten.
    
    Args:
        flashcards: Liste von Dictionaries mit 'frage' und 'antwort' Keys
        output_path: Pfad zur Ausgabedatei
        
    Returns:
        Anzahl der exportierten Karteikarten
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    exported_count = 0
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        for card in flashcards:
            frage = card.get('frage', '').strip()
            antwort = card.get('antwort', '').strip()
            
            if not frage or not antwort:
                continue
            
            # Tabs in Frage/Antwort escapen
            frage = frage.replace('\t', ' ')
            antwort = antwort.replace('\t', ' ')
            
            # Zeilenumbrüche escapen
            antwort = antwort.replace('\n', '\\n')
            
            f.write(f"{frage}\t{antwort}\n")
            exported_count += 1
    
    return exported_count


if __name__ == "__main__":
    # Test
    test_cards = [
        {
            "frage": "Erkläre das Kano-Modell und die drei Arten von Produktmerkmalen.",
            "antwort": """Kundenzufriedenheit hängt von drei Arten von Produktmerkmalen ab:

1. Threshold Attributes (Basismerkmale/Muss-Leistung):
   - Grundanforderungen (z.B. Bremsen im Auto)
   - Erfüllung garantiert keine höhere Zufriedenheit
   - Fehlen führt zu Unzufriedenheit

2. Performance Attributes (Leistungsmerkmale):
   - Je besser, desto zufriedener (lineare Erhöhung)
   - Beispiel: Kraftstoffverbrauch

3. Excitement Attributes (Begeisterungsmerkmale):
   - Unerwartete Attribute für latente Bedürfnisse
   - Beispiel: automatische Einparkhilfe

Dynamik: Excitement-Attribute werden mit der Zeit zu Threshold-Attributen (Gewöhnungseffekt)"""
        }
    ]
    
    count = export_to_tsv(test_cards, "test_output.tsv")
    print(f"✓ {count} Karteikarten exportiert nach test_output.tsv")
