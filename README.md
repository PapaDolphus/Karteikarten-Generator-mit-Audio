# 🎓 AI Flashcard Generator

Ein intelligentes Tool, das aus PDF-Vorlesungsunterlagen (BWL, Statistik, etc.) automatisch hochwertige Anki-Karteikarten generiert – inklusive **Audio-Erklärungen**.

Es nutzt **OpenAI** (GPT-4o, TTS) und **Google Gemini** (gemini-3-pro) parallel, um die besten Erklärungen zu generieren und kombiniert diese.

## Features

- **🧠 Dual-LLM Generierung**: Kombiniert die Stärken von OpenAI und Gemini für maximale Qualität.
- **📚 Zwei Lern-Modi**:
  - `Standard`: Für Konzepte, Modelle und Theorien.
  - `Quantitativ`: Für Formeln, Rechnungen und Statistik (mit Rechenwegen!).
- **🎧 Audio-Erklärungen**: Generiert natürliche, podcast-artige Erklärungen zu jeder Karte (TTS).
- **🎛️ Interaktive CLI**: Einfache Bedienung ohne komplexe Befehle.
- **🔄 Anki-Import**: Exportiert direkt als TSV für den Import in Anki (HTML-formatiert).

## Installation

1. Clone das Repository:
   ```bash
   git clone https://github.com/dein-user/karteikarten-generator.git
   cd karteikarten-generator
   ```

2. Führe das Setup-Skript aus (MacOS/Linux):
   ```bash
   ./setup.sh
   ```
   *Alternativ manuell:* `pip install -r requirements.txt`

3. Erstelle eine `.env` Datei mit deinen API-Keys:
   ```env
   OPENAI_API_KEY=sk-...
   GOOGLE_API_KEY=AIza...
   ```

## Nutzung

Starte das Tool interaktiv:

```bash
python3 main.py vorlesung.pdf -i
```

Oder direkt per CLI:

```bash
# Standard-Modus
python3 main.py vorlesung.pdf

# Mathe/Statistik-Modus
python3 main.py statistik.pdf --mode quantitative

# Mit Audio
python3 main.py vorlesung.pdf --audio --voice nova
```

## Voraussetzungen

- Python 3.8+
- OpenAI API Key
- Google Gemini API Key
- `ffmpeg` (optional, falls pyanote audio genutzt wird, hier nicht nötig)

## Lizenz

MIT
