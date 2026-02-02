"""
Audio-Generator für Karteikarten

Transformiert Karteikarten in natürliche Audio-Erklärungen mit Gesprächscharakter.
Nutzt OpenAI GPT für die Text-Transformation und OpenAI TTS für die Audio-Generierung.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Umgebungsvariablen laden
load_dotenv()

# System-Prompt für die Transformation in Gesprächs-Stil
EXPLANATION_SYSTEM_PROMPT = """Du bist ein freundlicher und kompetenter Tutor, der Studierenden komplexe BWL-Konzepte erklärt. 
Deine Aufgabe ist es, eine Karteikarte in eine natürliche Audio-Erklärung zu verwandeln.

STIL-ANWEISUNGEN:
1. Beginne mit einer lockeren Einleitung wie "Lass uns mal über X sprechen..." oder "Heute schauen wir uns an..."
2. Erkläre das Konzept Schritt für Schritt in einfacher, verständlicher Sprache
3. Füge konkrete, alltagsnahe Beispiele hinzu - das macht es greifbar!
4. Nutze natürliche Übergänge:
   - "Stell dir vor..."
   - "Das bedeutet praktisch..."
   - "Ein gutes Beispiel dafür wäre..."
   - "Kurz gesagt..."
5. Schließe mit einer kurzen, einprägsamen Zusammenfassung ab

WICHTIGE REGELN:
- Der Text wird VORGELESEN, also:
  - KEINE Aufzählungszeichen oder Nummerierungen
  - KEINE Formatierung wie Fettdruck oder Überschriften
  - Schreibe alles als fließenden Text
- Halte den Text zwischen 150-300 Wörtern für eine angenehme Länge
- Sei warmherzig und ermutigend, nicht trocken oder akademisch
- Sprich den Zuhörer direkt an ("du", "dir")

OUTPUT: Nur der fertige Erklärungstext, nichts anderes."""


class AudioGenerator:
    """Generiert Audio-Erklärungen aus Karteikarten."""
    
    def __init__(self, model: str = "gpt-4o-mini", voice: str = "nova"):
        """
        Initialisiert den Audio-Generator.
        
        Args:
            model: OpenAI Modell für Text-Transformation (Standard: gpt-4o-mini für Kosteneffizienz)
            voice: TTS-Stimme (alloy, echo, fable, onyx, nova, shimmer)
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY Umgebungsvariable nicht gesetzt!")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.voice = voice
    
    def transform_to_explanation(self, frage: str, antwort: str) -> str:
        """
        Transformiert eine Karteikarte in einen natürlichen Erklärungstext.
        
        Args:
            frage: Die Frage der Karteikarte
            antwort: Die Antwort der Karteikarte
            
        Returns:
            Natürlicher Erklärungstext für TTS
        """
        # HTML-Tags aus der Antwort entfernen (von TSV-Export)
        antwort_clean = antwort.replace('<br>', '\n').replace('<br/>', '\n')
        
        user_prompt = f"""Verwandle diese Karteikarte in eine angenehme Audio-Erklärung:

FRAGE: {frage}

ANTWORT:
{antwort_clean}

Erstelle daraus einen natürlich klingenden Erklärungstext."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": EXPLANATION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,  # Etwas kreativer für natürlicheren Ton
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"  ⚠️ Fehler bei Text-Transformation: {e}")
            # Fallback: Einfache Kombination von Frage und Antwort
            return f"{frage}\n\n{antwort_clean}"
    
    def generate_audio(self, text: str, output_path: str) -> bool:
        """
        Generiert eine MP3-Audio-Datei aus Text.
        
        Args:
            text: Der zu sprechende Text
            output_path: Pfad zur Ausgabe-MP3-Datei
            
        Returns:
            True wenn erfolgreich, False bei Fehler
        """
        try:
            response = self.client.audio.speech.create(
                model="tts-1-hd",  # HD-Qualität für besseren Klang
                voice=self.voice,
                input=text,
                speed=1.20  # Schneller für angenehmes Lerntempo
            )
            
            # Audio-Datei speichern
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Audio-Inhalt direkt schreiben
            output_file.write_bytes(response.content)
            return True
            
        except Exception as e:
            print(f"  ⚠️ Fehler bei Audio-Generierung: {e}")
            return False
    
    def process_flashcard(self, frage: str, antwort: str, output_path: str) -> bool:
        """
        Verarbeitet eine einzelne Karteikarte zu Audio.
        
        Args:
            frage: Die Frage der Karteikarte
            antwort: Die Antwort der Karteikarte
            output_path: Pfad zur Ausgabe-MP3-Datei
            
        Returns:
            True wenn erfolgreich, False bei Fehler
        """
        # 1. Text transformieren
        explanation = self.transform_to_explanation(frage, antwort)
        
        # 2. Audio generieren
        return self.generate_audio(explanation, output_path)
    
    def process_flashcards(self, flashcards: List[Dict[str, str]], 
                           output_dir: str, 
                           prefix: str = "karte") -> int:
        """
        Verarbeitet eine Liste von Karteikarten zu Audio-Dateien.
        
        Args:
            flashcards: Liste von Dictionaries mit 'frage' und 'antwort' Keys
            output_dir: Verzeichnis für die Audio-Dateien
            prefix: Präfix für Dateinamen
            
        Returns:
            Anzahl erfolgreich generierter Audio-Dateien
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        successful = 0
        total = len(flashcards)
        
        for i, card in enumerate(flashcards, 1):
            frage = card.get('frage', '')
            antwort = card.get('antwort', '')
            
            if not frage or not antwort:
                continue
            
            # Kurze Beschreibung für Dateinamen erstellen
            safe_name = self._sanitize_filename(frage[:50])
            filename = f"{prefix}_{i:03d}_{safe_name}.mp3"
            filepath = output_path / filename
            
            print(f"  🎙️ [{i}/{total}] Generiere Audio: {frage[:40]}...")
            
            if self.process_flashcard(frage, antwort, str(filepath)):
                successful += 1
                print(f"    ✓ Gespeichert: {filename}")
            else:
                print(f"    ✗ Fehlgeschlagen")
        
        return successful
    
    def _sanitize_filename(self, text: str) -> str:
        """Entfernt ungültige Zeichen aus Dateinamen."""
        # Nur Buchstaben, Zahlen und Unterstriche behalten
        sanitized = re.sub(r'[^\w\s-]', '', text)
        sanitized = re.sub(r'[-\s]+', '_', sanitized)
        return sanitized.strip('_').lower()


def load_flashcards_from_tsv(tsv_path: str) -> List[Dict[str, str]]:
    """
    Lädt Karteikarten aus einer TSV-Datei.
    
    Args:
        tsv_path: Pfad zur TSV-Datei
        
    Returns:
        Liste von Dictionaries mit 'frage' und 'antwort' Keys
    """
    flashcards = []
    
    with open(tsv_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('\t')
            if len(parts) >= 2:
                flashcards.append({
                    'frage': parts[0],
                    'antwort': parts[1]
                })
    
    return flashcards


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generiert Audio-Erklärungen aus Karteikarten (TSV)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
    python3 audio_generator.py final_karteikarten.tsv
    python3 audio_generator.py karten.tsv --voice echo
    python3 audio_generator.py karten.tsv --output ./meine_audios --voice fable
        """
    )
    
    parser.add_argument("tsv", nargs="?", help="Pfad zur TSV-Datei mit Karteikarten")
    parser.add_argument("-o", "--output", default="./audio_output",
                        help="Ausgabeverzeichnis für Audio-Dateien (Standard: ./audio_output)")
    parser.add_argument("-v", "--voice",
                        choices=["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                        default="nova",
                        help="TTS-Stimme (Standard: nova)")
    
    args = parser.parse_args()
    
    print("\n🎧 Audio-Generator für Karteikarten")
    print("=" * 50)
    
    if args.tsv:
        # TSV-Datei verarbeiten
        print(f"📄 Lade Karteikarten aus: {args.tsv}")
        flashcards = load_flashcards_from_tsv(args.tsv)
        print(f"  ✓ {len(flashcards)} Karteikarten geladen")
        
        print(f"\n🎙️ Stimme: {args.voice}")
        print(f"📁 Ausgabe: {args.output}\n")
        
        try:
            generator = AudioGenerator(voice=args.voice)
            count = generator.process_flashcards(flashcards, args.output)
            print(f"\n✅ {count} Audio-Dateien erfolgreich generiert!")
        except ValueError as e:
            print(f"❌ Fehler: {e}")
            
    else:
        # Demo-Modus
        print("🔬 Demo-Modus (keine TSV-Datei angegeben)")
        print(f"🎙️ Stimme: {args.voice}\n")
        
        test_card = {
            "frage": "Was ist das Kano-Modell?",
            "antwort": """Das Kano-Modell beschreibt drei Arten von Produktmerkmalen:

1. Basismerkmale (Threshold): Müssen erfüllt sein, z.B. Bremsen im Auto.
2. Leistungsmerkmale (Performance): Je besser, desto zufriedener, z.B. Kraftstoffverbrauch.
3. Begeisterungsmerkmale (Excitement): Unerwartete Features, z.B. automatische Einparkhilfe.

Dynamik: Begeisterungsmerkmale werden mit der Zeit zu Basismerkmalen."""
        }
        
        try:
            generator = AudioGenerator(voice=args.voice)
            
            print("📝 Transformiere Karteikarte zu Erklärungstext...")
            explanation = generator.transform_to_explanation(test_card["frage"], test_card["antwort"])
            print(f"\n--- Erklärungstext ---\n{explanation}\n---\n")
            
            output_file = "./test_audio.mp3"
            print(f"🎙️ Generiere Audio: {output_file}")
            
            if generator.generate_audio(explanation, output_file):
                print(f"✅ Audio erfolgreich erstellt: {output_file}")
            else:
                print("❌ Audio-Generierung fehlgeschlagen")
                
        except ValueError as e:
            print(f"❌ Fehler: {e}")

