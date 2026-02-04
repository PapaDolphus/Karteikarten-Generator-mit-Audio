#!/bin/bash
# Setup-Skript für Karteikarten-Generator
# 


echo "🔧 Karteikarten-Generator Setup"
echo "================================"
echo ""

# Prüfe ob Python 3 verfügbar ist
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 nicht gefunden. Bitte installiere Python 3."
    exit 1
fi

echo "✓ Python 3 gefunden: $(python3 --version)"
echo ""

# Installiere Abhängigkeiten mit --user flag
echo "📦 Installiere Abhängigkeiten..."
python3 -m pip install --user pymupdf openai google-generativeai python-dotenv

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Setup abgeschlossen!"
    echo ""
    echo "📋 Nächste Schritte:"
    echo "   1. Setze deine API-Keys als Umgebungsvariablen:"
    echo "      export OPENAI_API_KEY='dein-openai-key'"
    echo "      export GOOGLE_API_KEY='dein-google-key'"
    echo ""
    echo "   2. Starte das Programm:"
    echo "      python3 main.py deine_datei.pdf"
    echo ""
else
    echo ""
    echo "❌ Installation fehlgeschlagen."
    echo "   Versuche: pip3 install --user -r requirements.txt"
fi
