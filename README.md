# 🎓 AI Flashcard Generator & Audio Tutor

Dies ist ein leistungsstarkes Tool-Set, das **Vorlesungsunterlagen (PDFs)** automatisch in hochwertige **Anki-Karteikarten** verwandelt und zusätzlich natürliche, podcast-artige **Audio-Erklärungen** (Tutor-style) generiert.

Es kombiniert die Stärken von **OpenAI (GPT-4o)** und **Google Gemini** für maximale Qualität.

---

## ✨ Features

### 🧠 Intelligente Generierung
- **Dual-LLM Strategie**: Nutzt OpenAI und Google Gemini parallel für robustere Ergebnisse.
- **Kontext-Verständnis**: Extrahiert Kapitelstrukturen aus PDFs für thematisch saubere Karten.
- **Zwei Lern-Modi**:
  - `Standard`: Fokus auf Konzepte, Definitionen, Modelle (BWL, Theorie).
  - `Quantitativ`: Fokus auf Rechenwege, Formeln und Statistik (mit Schritt-für-Schritt Lösungen).

### 🎧 Audio-Tutor (Learning on the go)
- **Natürliche Sprache**: Verwandelt trockene Karteikarten in lockere Erklärungen ("Lass uns mal das Kano-Modell anschauen...").
- **High-Quality TTS**: Nutzt OpenAI's HD-Stimmen (Alloy, Echo, Nova, etc.).
- **Resume-Funktion**: Abgebrochene Generierung kann nahtlos fortgesetzt werden.

### 🛠️ Flexibilität
- **Interaktiver Modus**: Einfaches Menü für alle Einstellungen.
- **CLI-Power**: Volle Kontrolle über Kommandozeilen-Argumente für Automatisierung.
- **Video-Pipeline (Beta)**: Experimentelle Unterstützung für Remotion-Video-Erstellung.

---

## 🚀 Installation

### 1. Repository Klonen
```bash
git clone https://github.com/dein-user/karteikarten-generator.git
cd karteikarten-generator
```

### 2. Abhängigkeiten installieren
Nutze das Setup-Skript (empfohlen für Mac/Linux):
```bash
./setup.sh
```
*Oder manuell:* `pip install -r requirements.txt`

### 3. API-Keys konfigurieren
Erstelle eine Datei namens `.env` im Hauptverzeichnis:

```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxx
GOOGLE_API_KEY=AIzaSyDxxxxxxxxxxxxxxxxx
```
*(Die `.gitignore` sorgt dafür, dass diese Datei nicht veröffentlicht wird.)*

---

## 🎮 Nutzung (Quick Start)

Der einfachste Weg ist der **Interaktive Modus**. Lege dein PDF in den Ordner und starte:

```bash
python3 main.py vorlesung.pdf -i
```

Das Skript führt dich durch alle Schritte:
1.  **Modus wählen** (Standard vs. Quantitativ)
2.  **KI wählen** (Beide, nur OpenAI oder nur Gemini)
3.  **Menge begrenzen** (Optional, z.B. nur 50 Karten)
4.  **Audio** aktivieren & Stimme wählen

---

## 🤓 Experten-Modus (CLI Referenz)

Du kannst alle Optionen auch direkt übergeben:

### Grundbefehle
```bash
# Standard-Generierung
python3 main.py script.pdf

# Mathe-Modus & nur Gemini nutzen
python3 main.py statistik.pdf --mode quantitative --provider gemini

# Limitieren auf ca. 30 Karten (testweise)
python3 main.py script.pdf --max-cards 30
```

### Audio-Generator Tools
Falls du schon eine TSV-Datei hast (z.B. `final_karteikarten.tsv`) und nur Audios willst:

```bash
# Audios generieren
python3 audio_generator.py final_karteikarten.tsv --voice nova

# Fortsetzen ab Karte 51 (Resume nach Abbruch)
python3 audio_generator.py final_karteikarten.tsv --start 51
```

### Verfügbare Argumente (`main.py`)
| Argument | Beschreibung |
|---|---|
| `-i`, `--interactive` | Startet das interaktive Menü |
| `-m`, `--mode` | `standard` oder `quantitative` |
| `--provider` | `openai`, `gemini` oder `both` |
| `--max-cards` | Ungefähres Limit für die Gesamtanzahl |
| `--voice` | TTS-Stimme (`alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`) |
| `--audio` | Aktiviert Audio-Generierung direkt nach Kartenerstellung |

---

## 📥 Import in Anki

Um die generierten Karten (`.tsv` Datei) in Anki zu nutzen:

1.  Öffne **Anki** am PC/Mac.
2.  Klicke auf **Datei** -> **Importieren**.
3.  Wähle die generierte `.tsv` Datei aus.
4.  **WICHTIG:** Stelle sicher, dass "HTML in Feldern zulassen" aktiviert ist.
5.  Zuweisung der Felder:
    - Feld 1 -> Vorderseite (Frage)
    - Feld 2 -> Rückseite (Antwort)
6.  Klicke auf **Importieren**.

*Tipp für Audio:* Kopiere die generierten `.mp3` Dateien in deinen Anki-Medienordner, wenn du sie direkt in Anki verknüpfen willst (aktuell sind die Audios für die Nutzung als "Podcast" gedacht).

---

## 📂 Projektstruktur

- **`main.py`**: Der "Chef". Steuert den Ablauf, ruft Parser und KIs auf.
- **`llm_clients.py`**: Enthält die Logik für OpenAI und Gemini (Prompts, API-Calls).
- **`pdf_parser.py`**: Zerlegt PDFs intelligent in Kapitel (erkennt Überschriften).
- **`audio_generator.py`**: Spezialist für Text-zu-Sprache Transformation.
- **`tsv_exporter.py`**: Speichert die Ergebnisse als Anki-kompatible Datei.
- **`video_pipeline.py` (Beta)**: Erstellt JSON-Daten für automatisierte Lernvideos.

---

## ⚠️ Bekannte Hinweise

- **PDF-Qualität**: Das Tool funktioniert am besten mit "echten" PDFs (Text markierbar). Eingescannte Bilder funktionieren nicht ohne OCR.
- **Kosten**: Die Nutzung der APIs (besonders GPT-4o und TTS-1-HD) kostet Geld. Behalte dein OpenAI/Google Guthaben im Blick.

## 📜 Lizenz

MIT License - Feel free to fork and modify!
