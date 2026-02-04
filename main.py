#!/usr/bin/env python3
"""
Karteikarten-Generator aus PDF-Dateien

Generiert umfassende Lernkarteikarten aus PDF-Dokumenten mithilfe von
OpenAI und Google Gemini. Die Karteikarten decken vollständige Konzepte
und Systeme ab, optimiert für BWL-Studierende.

Unterstützt zwei Modi:
- standard: Für konzeptbasierte BWL-Inhalte (Modelle, Systeme, Theorien)
- quantitative: Für Statistik, Rechnungen, Formeln, Projektmanagement

Verwendung:
    python main.py <pdf_datei> [--output <ausgabe.tsv>] [--mode quantitative]
"""

import argparse
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

from pdf_parser import extract_sections_from_pdf, extract_text_only, extract_text_as_chunks
from llm_clients import OpenAIClient, GeminiClient, combine_flashcards
from tsv_exporter import export_to_tsv
from audio_generator import AudioGenerator


def process_section(section_title: str, section_content: str, 
                    openai_client: OpenAIClient, gemini_client: GeminiClient,
                    mode: str = "standard", provider: str = "both", limit: int = None) -> List[Dict[str, str]]:
    """
    Verarbeitet einen Abschnitt mit den gewählten LLMs.
    
    Args:
        section_title: Überschrift des Abschnitts
        section_content: Inhalt des Abschnitts
        openai_client: OpenAI Client
        gemini_client: Gemini Client
        mode: Modus für die Generierung
        provider: 'openai', 'gemini' oder 'both'
        limit: Maximale Anzahl Karten (pro LLM)
    """
    print(f"  📝 Generiere Karteikarten für: {section_title[:50]}...")
    
    openai_cards = []
    gemini_cards = []
    
    # LLM-Aufrufe parallel planen
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {}
        
        if provider in ["openai", "both"]:
            # Bei Single-Provider und gesetztem Limit: Volles Limit nutzen
            # Bei "both": Limit pro LLM, später kombinieren
            p_limit = limit
            futures[executor.submit(openai_client.generate_flashcards, section_title, section_content, mode, p_limit)] = "openai"
            
        if provider in ["gemini", "both"]:
            p_limit = limit
            futures[executor.submit(gemini_client.generate_flashcards, section_title, section_content, mode, p_limit)] = "gemini"
        
        for future in as_completed(futures):
            api_name = futures[future]
            try:
                cards = future.result()
                if api_name == "openai":
                    openai_cards = cards
                    print(f"    ✓ OpenAI: {len(cards)} Karten")
                else:
                    gemini_cards = cards
                    print(f"    ✓ Gemini: {len(cards)} Karten")
            except Exception as e:
                print(f"    ✗ {api_name} Fehler: {e}")
    
    # Ergebnisse kombinieren
    combined = combine_flashcards(openai_cards, gemini_cards)
    print(f"    → {len(combined)} Karten nach Kombination")
    
    return combined


def main():
    parser = argparse.ArgumentParser(
        description="Generiert umfassende Karteikarten aus PDF-Dateien",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
    python main.py vorlesung.pdf
    python main.py skript.pdf --output meine_karten.tsv
    python main.py statistik.pdf --mode quantitative
    python main.py kapitel1.pdf -o kapitel1_karten.tsv -m quantitative

Modi:
    standard     - Für konzeptbasierte Inhalte (Modelle, Systeme, Theorien)
    quantitative - Für Statistik, Rechnungen, Formeln, PM-Methoden

Umgebungsvariablen:
    OPENAI_API_KEY    - OpenAI API Schlüssel
    GOOGLE_API_KEY    - Google Gemini API Schlüssel (oder GEMINI_API_KEY)
        """
    )
    
    parser.add_argument("pdf", help="Pfad zur PDF-Datei")
    parser.add_argument("-o", "--output", 
                        help="Pfad zur Ausgabe-TSV-Datei (Standard: <pdf_name>_karteikarten.tsv)")
    parser.add_argument("-m", "--mode", 
                        choices=["standard", "quantitative"],
                        default="standard",
                        help="Modus: 'standard' für Konzepte, 'quantitative' für Statistik/Rechnungen")
    parser.add_argument("--no-sections", action="store_true",
                        help="Ignoriere Überschriften-Erkennung, behandle gesamte PDF als einen Abschnitt")
    parser.add_argument("-a", "--audio", action="store_true",
                        help="Generiere zusätzlich Audio-Erklärungen (MP3)")
    parser.add_argument("--audio-dir",
                        help="Verzeichnis für Audio-Dateien (Standard: <pdf_name>_audio/)")
    parser.add_argument("--voice",
                        choices=["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                        default="nova",
                        help="TTS-Stimme für Audio (Standard: nova)")
    parser.add_argument("--provider",
                        choices=["openai", "gemini", "both"],
                        default="both",
                        help="Welche KI verwendet werden soll (Standard: both)")
    parser.add_argument("--max-cards", type=int,
                        help="Ungefähre Obergrenze für die Anzahl der Karteikarten")
    parser.add_argument("-i", "--interactive", action="store_true",
                        help="Interaktiver Modus: Fragt Einstellungen beim Start ab")
    
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf)
    
    if not pdf_path.exists():
        print(f"❌ Fehler: PDF-Datei nicht gefunden: {pdf_path}")
        sys.exit(1)
    
    # Output-Pfad bestimmen
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = pdf_path.with_name(f"{pdf_path.stem}_karteikarten.tsv")
    
    # Interaktiver Modus: Einstellungen abfragen
    if args.interactive:
        print("\n🎛️  Interaktive Konfiguration")
        print("---------------------------")
        
        # 1. Modus abfragen
        print("\nWelcher Modus soll verwendet werden?")
        print("  1) Standard (Konzepte, Modelle, Theorien)")
        print("  2) Quantitativ (Rechnungen, Formeln, Statistik)")
        while True:
            choice = input("Auswahl (1/2) [1]: ").strip()
            if choice == "1" or choice == "":
                args.mode = "standard"
                break
            elif choice == "2":
                args.mode = "quantitative"
                break
                
        # 2. KI-Auswahl (Provider)
        print("\nWelche KI soll verwendet werden?")
        print("  1) Beide (Empfohlen für beste Qualität)")
        print("  2) Nur OpenAI (GPT-4o)")
        print("  3) Nur Google Gemini (Flash/Pro)")
        while True:
            prov_choice = input("Auswahl (1-3) [1]: ").strip()
            if prov_choice == "1" or prov_choice == "":
                args.provider = "both"
                break
            elif prov_choice == "2":
                args.provider = "openai"
                break
            elif prov_choice == "3":
                args.provider = "gemini"
                break

        # 3. Mengenbegrenzung
        print("\nWie viele Karteikarten sollen UNGEFÄHR insgesamt erstellt werden?")
        print("  (Leer lassen für Maximum / keine Begrenzung)")
        limit_input = input("Anzahl (z.B. 50): ").strip()
        if limit_input and limit_input.isdigit():
            args.max_cards = int(limit_input)

        # 4. Audio abfragen
        print("\nSollen Audio-Erklärungen generiert werden?")
        while True:
            audio_choice = input("Audio generieren? (j/n) [n]: ").strip().lower()
            if audio_choice == "j" or audio_choice == "ja" or audio_choice == "y":
                args.audio = True
                
                # Stimme abfragen wenn Audio aktiv
                print("\nWelche Stimme soll verwendet werden?")
                voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
                for i, v in enumerate(voices, 1):
                    print(f"  {i}) {v}")
                
                v_choice = input(f"Stimme wählen (1-6) [5 ({args.voice})]: ").strip()
                if v_choice and v_choice.isdigit() and 1 <= int(v_choice) <= 6:
                    args.voice = voices[int(v_choice)-1]
                break
            elif audio_choice == "n" or audio_choice == "nein" or audio_choice == "":
                args.audio = False
                break
    
    mode_emoji = "🧮" if args.mode == "quantitative" else "📚"
    mode_label = "Quantitativ (Rechnungen/Formeln)" if args.mode == "quantitative" else "Standard (Konzepte/Systeme)"
    
    print(f"\n🎓 Karteikarten-Generator")
    print(f"{'='*50}")
    print(f"📄 Eingabe:  {pdf_path}")
    print(f"📁 Ausgabe:  {output_path}")
    print(f"{mode_emoji} Modus:    {mode_label}")
    print(f"🤖 KI:       {args.provider.upper()}")
    if args.max_cards:
        print(f"📉 Limit:    ca. {args.max_cards} Karten")
    print()
    
    # LLM Clients initialisieren
    print("🔌 Initialisiere LLM Clients...")
    start_openai = args.provider in ["openai", "both"]
    start_gemini = args.provider in ["gemini", "both"]

    if start_openai:
        try:
            openai_client = OpenAIClient()
            print(f"  ✓ OpenAI bereit (Modell: {openai_client.model})")
        except ValueError as e:
            print(f"  ✗ OpenAI: {e}")
            sys.exit(1)
    else:
        openai_client = None
    
    if start_gemini:
        try:
            gemini_client = GeminiClient()
            print(f"  ✓ Gemini bereit (Modell: {gemini_client.model_name})")
        except ValueError as e:
            print(f"  ✗ Gemini: {e}")
            sys.exit(1)
    else:
        gemini_client = None
    
    print()
    
    # PDF verarbeiten
    print("📖 Extrahiere Inhalte aus PDF...")
    
    if args.no_sections:
        # Gesamte PDF als einen Abschnitt behandeln
        full_text = extract_text_only(str(pdf_path))
        sections = {"Gesamtinhalt": full_text}
    elif args.mode == "quantitative":
        # Bei quantitativen PDFs in Chunks aufteilen für umfassende Abdeckung
        sections = extract_text_as_chunks(str(pdf_path), chunk_size=4000)
        print(f"  ℹ️  Quantitativer Modus: PDF in {len(sections)} Teile aufgeteilt")
    else:
        sections = extract_sections_from_pdf(str(pdf_path))
    
    print(f"  ✓ {len(sections)} Abschnitt(e) gefunden")
    print()
    
    if not sections:
        print("❌ Keine Inhalte in der PDF gefunden!")
        sys.exit(1)
    
    # Karteikarten für jeden Abschnitt generieren
    print("🤖 Generiere Karteikarten mit OpenAI und Gemini...")
    print()
    
    all_flashcards = []
    
    # Limit pro Abschnitt berechnen
    limit_per_section = None
    if args.max_cards:
        # Mindestens 3 Karten pro Abschnitt, aber insgesamt passend zum Limit
        calculated_limit = max(3, args.max_cards // len(sections))
        limit_per_section = calculated_limit
        print(f"ℹ️  Limitierung aktiv: ca. {limit_per_section} Karten pro Abschnitt")

    for i, (title, content) in enumerate(sections.items(), 1):
        print(f"[{i}/{len(sections)}] Verarbeite: {title}")
        
        if len(content.strip()) < 50:
            print("  ⏭️  Übersprungen (zu wenig Inhalt)")
            continue
        
        cards = process_section(title, content, openai_client, gemini_client, args.mode, args.provider, limit_per_section)
        all_flashcards.extend(cards)
        print()
    
    if not all_flashcards:
        print("❌ Keine Karteikarten generiert!")
        sys.exit(1)
    
    # TSV exportieren
    print(f"💾 Exportiere {len(all_flashcards)} Karteikarten...")
    exported = export_to_tsv(all_flashcards, str(output_path))
    
    print()
    print(f"{'='*50}")
    print(f"✅ Fertig! {exported} Karteikarten exportiert nach:")
    print(f"   {output_path}")
    print()
    print("📚 Import in Anki:")
    print("   1. Datei > Importieren")
    print("   2. TSV-Datei auswählen")
    print("   3. Feldtrenner: Tab")
    print("   4. HTML aktivieren (für Formatierung)")
    
    # Audio-Generierung wenn gewünscht
    if args.audio:
        print()
        print(f"{'='*50}")
        print("🎧 Audio-Erklärungen generieren...")
        print()
        
        # Audio-Verzeichnis bestimmen
        if args.audio_dir:
            audio_dir = Path(args.audio_dir)
        else:
            audio_dir = pdf_path.with_name(f"{pdf_path.stem}_audio")
        
        try:
            audio_generator = AudioGenerator(voice=args.voice)
            print(f"  ✓ Audio-Generator bereit (Stimme: {args.voice})")
            print(f"  📁 Ausgabe: {audio_dir}")
            print()
            
            audio_count = audio_generator.process_flashcards(
                all_flashcards, 
                str(audio_dir),
                prefix=pdf_path.stem
            )
            
            print()
            print(f"{'='*50}")
            print(f"✅ {audio_count} Audio-Dateien erstellt in:")
            print(f"   {audio_dir}")
            
        except ValueError as e:
            print(f"  ⚠️ Audio-Generierung übersprungen: {e}")


if __name__ == "__main__":
    main()
