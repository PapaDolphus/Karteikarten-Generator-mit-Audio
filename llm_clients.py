"""
LLM Clients für Karteikarten-Generierung

Wrapper für OpenAI und Google Gemini APIs mit optimierten Prompts
für die Erstellung umfassender BWL-Karteikarten.

Unterstützt zwei Modi:
- Standard: Für konzeptbasierte Inhalte mit Systemen und Modellen
- Quantitativ: Für statistische Inhalte, Rechnungen und Formeln
"""

import os
import json
import asyncio
from typing import List, Dict, Optional
from abc import ABC, abstractmethod
import re

from openai import OpenAI
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Umgebungsvariablen laden
load_dotenv()


# Standard System-Prompt für konzeptbasierte BWL-Karteikarten
FLASHCARD_SYSTEM_PROMPT = """Du bist ein Experte für die Erstellung von Lernkarteikarten für BWL-Studierende.
Deine Aufgabe ist es, aus dem gegebenen Lernmaterial umfassende und vollständige Karteikarten zu erstellen.

KRITISCHE REGELN - BEFOLGE DIESE GENAU:

1. VOLLSTÄNDIGKEIT: Jede Karteikarte MUSS ein ganzes System/Konzept/Modell VOLLSTÄNDIG erklären.
   - Wenn ein Modell 3 Komponenten hat, MÜSSEN alle 3 in der Antwort sein
   - Wenn es Phasen/Stufen gibt, MÜSSEN alle erklärt werden
   - Dynamiken, Zusammenhänge und Wechselwirkungen MÜSSEN enthalten sein

2. STRUKTUR DER ANTWORTEN:
   - Nutze Aufzählungen und Nummerierungen
   - Gliedere komplexe Antworten in logische Abschnitte
   - Jeder Teilaspekt bekommt eine eigene Zeile mit Erklärung

3. BEISPIELE: Füge relevante, praxisnahe Beispiele hinzu (z.B. "Beispiel: Kraftstoffverbrauch")

4. KEINE OBERFLÄCHLICHKEIT:
   - NIEMALS nur Begriffe nennen ohne Erklärung
   - NIEMALS unvollständige Listen
   - Jede Karte muss für sich allein verständlich sein

5. AUCH KLEINE DETAILS: Informationen die nicht in große Systeme passen, bekommen eigene Karten

6. FORMAT: Antworte NUR mit einem JSON-Array von Karteikarten:
[
  {"frage": "Erkläre das XYZ-Modell und seine Komponenten.", "antwort": "Das XYZ-Modell beschreibt...\\n\\n1. Erste Komponente: ...\\n2. Zweite Komponente: ...\\n\\nBeispiel: ..."},
  ...
]

WICHTIG: Die Antworten sollen so detailliert sein, dass man damit eine Prüfung bestehen kann!"""


# Quantitativer System-Prompt für Statistik, Rechnungen und Formeln
QUANTITATIVE_SYSTEM_PROMPT = """Du bist ein Experte für die Erstellung von Lernkarteikarten für Studierende im Bereich internationale/quantitative BWL, Statistik und Projektmanagement.
Deine Aufgabe ist es, aus dem gegebenen Lernmaterial umfassende Karteikarten zu erstellen, mit besonderem Fokus auf RECHNUNGEN, FORMELN und STATISTISCHE METHODEN.

KRITISCHE REGELN - BEFOLGE DIESE GENAU:

1. FORMELN UND RECHNUNGEN:
   - Jede relevante Formel bekommt eine eigene Karteikarte
   - Erkläre ALLE Variablen in der Formel
   - Zeige einen vollständigen RECHENWEG mit konkreten Zahlen
   - Beispiel: "NPV = Σ(CFt / (1+r)^t) - I0, wobei CFt = Cashflow in Periode t, r = Diskontierungszins, I0 = Anfangsinvestition"

2. STATISTISCHE KONZEPTE:
   - Erkläre WAS berechnet wird und WARUM
   - Zeige die Formel UND ein Rechenbeispiel
   - Interpretiere das Ergebnis (was bedeutet z.B. ein Korrelationskoeffizient von 0.8?)

3. TABELLEN UND DIAGRAMME:
   - Wenn im Text Statistiken erwähnt werden, erstelle Karten die diese Werte abfragen
   - Erstelle Karten zu Interpretationen von Kennzahlen

4. STRUKTUR DER ANTWORTEN:
   - Formel zuerst
   - Dann Variablenerklärung
   - Dann Rechenbeispiel mit echten Zahlen
   - Dann Interpretation

5. PROJEKTMANAGEMENT-METHODEN:
   - Critical Path Method (CPM), PERT, Earned Value Analysis etc.
   - Immer mit vollständigem Rechenbeispiel

6. FORMAT: Antworte NUR mit einem JSON-Array von Karteikarten:
[
  {"frage": "Wie berechnet man den Net Present Value (NPV)?", "antwort": "Der NPV berechnet den Barwert aller zukünftigen Cashflows abzüglich der Anfangsinvestition.\\n\\nFormel: NPV = Σ(CFt / (1+r)^t) - I0\\n\\nVariablen:\\n- CFt = Cashflow in Periode t\\n- r = Diskontierungszins\\n- I0 = Anfangsinvestition\\n\\nBeispielrechnung:\\n- I0 = 10.000€, CF1 = 4.000€, CF2 = 5.000€, CF3 = 6.000€, r = 10%\\n- NPV = 4000/1.1 + 5000/1.21 + 6000/1.331 - 10000\\n- NPV = 3636 + 4132 + 4507 - 10000 = 2.275€\\n\\nInterpretation: NPV > 0 → Investition lohnt sich"},
  ...
]

WICHTIG: Jede Karte mit Rechnung muss einen VOLLSTÄNDIGEN RECHENWEG mit konkreten Zahlen enthalten!"""


class LLMClient(ABC):
    """Abstrakte Basisklasse für LLM-Clients."""
    
    @abstractmethod
    def generate_flashcards(self, section_title: str, section_content: str, mode: str = "standard", limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Generiert Karteikarten aus einem Abschnitt."""
        pass
    
    def _get_system_prompt(self, mode: str) -> str:
        """Gibt den passenden System-Prompt basierend auf dem Modus zurück."""
        if mode == "quantitative":
            return QUANTITATIVE_SYSTEM_PROMPT
        return FLASHCARD_SYSTEM_PROMPT
    
    def _build_user_prompt(self, section_title: str, section_content: str, mode: str, limit: Optional[int] = None) -> str:
        """Erstellt den User-Prompt basierend auf Modus und Limit."""
        if limit:
            limit_instruction = f"WICHTIG: Erstelle MAXIMAL {limit} Karteikarten für diesen Abschnitt! Konzentriere dich auf die {limit} wichtigsten Punkte."
        else:
            limit_instruction = "Erstelle so viele Karteikarten wie nötig, um ALLE Informationen vollständig abzudecken."

        if mode == "quantitative":
            return f"""Erstelle umfassende Karteikarten für folgenden Abschnitt.
FOKUS: Rechnungen, Formeln, statistische Methoden und quantitative Konzepte.
{limit_instruction}

ÜBERSCHRIFT: {section_title}

INHALT:
{section_content}

Erstelle Karteikarten für JEDE Formel und JEDE Rechenmethode.
Jede Karte mit Rechnung MUSS einen vollständigen Rechenweg mit konkreten Zahlen enthalten!"""
        else:
            return f"""Erstelle umfassende Karteikarten für folgenden Abschnitt:
{limit_instruction}

ÜBERSCHRIFT: {section_title}

INHALT:
{section_content}

Jede Karte muss ein komplettes Konzept/System erklären - keine oberflächlichen Fragen!"""
    
    def _parse_response(self, response_text: str) -> List[Dict[str, str]]:
        """Parst die JSON-Antwort des LLMs."""
        # Entferne führende/nachfolgende Whitespaces
        text = response_text.strip()
        
        # Versuche JSON-Block aus Markdown-Code-Block zu extrahieren
        # Suche nach ```json ... ``` oder ``` ... ```
        code_block_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if code_block_match:
            text = code_block_match.group(1).strip()
        
        # Finde das JSON-Array (von [ bis ])
        # Suche nach dem äußersten Array
        start = text.find('[')
        if start != -1:
            # Finde das korrespondierende schließende ]
            bracket_count = 0
            end = start
            for i, char in enumerate(text[start:], start):
                if char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end = i + 1
                        break
            
            json_text = text[start:end]
            
            try:
                cards = json.loads(json_text)
                if isinstance(cards, list):
                    return [c for c in cards if "frage" in c and "antwort" in c]
            except json.JSONDecodeError as e:
                print(f"    [DEBUG] JSON Parse Error: {e}")
        
        return []


class OpenAIClient(LLMClient):
    """OpenAI API Client für Karteikarten-Generierung."""
    
    def __init__(self, model: str = "gpt-5.2"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY Umgebungsvariable nicht gesetzt!")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def generate_flashcards(self, section_title: str, section_content: str, mode: str = "standard", limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Generiert Karteikarten mit OpenAI."""
        
        system_prompt = self._get_system_prompt(mode)
        user_prompt = self._build_user_prompt(section_title, section_content, mode, limit)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Niedrig für konsistente, sachliche Antworten
                max_completion_tokens=16000
            )
            
            response_text = response.choices[0].message.content
            cards = self._parse_response(response_text)
            if not cards:
                print(f"    [DEBUG OpenAI] Antwort konnte nicht geparst werden. Erste 500 Zeichen:")
                print(f"    {response_text[:500]}...")
            return cards
            
        except Exception as e:
            print(f"OpenAI Fehler: {e}")
            return []


class GeminiClient(LLMClient):
    """Google Gemini API Client für Karteikarten-Generierung."""
    
    def __init__(self, model: str = "gemini-3-pro-preview"):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY oder GEMINI_API_KEY Umgebungsvariable nicht gesetzt!")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = model
    
    def generate_flashcards(self, section_title: str, section_content: str, mode: str = "standard", limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Generiert Karteikarten mit Gemini."""
        
        system_prompt = self._get_system_prompt(mode)
        user_content = self._build_user_prompt(section_title, section_content, mode, limit)
        
        # System-Prompt in den User-Content integrieren (alter Stil für bessere Ergebnisse)
        full_content = f"{system_prompt}\n\n---\n\n{user_content}"
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_content,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=16000
                )
            )
            
            cards = self._parse_response(response.text)
            if not cards:
                print(f"    [DEBUG Gemini] Antwort konnte nicht geparst werden. Erste 500 Zeichen:")
                print(f"    {response.text[:500]}...")
            return cards
            
        except Exception as e:
            print(f"Gemini Fehler: {e}")
            return []


def combine_flashcards(openai_cards: List[Dict], gemini_cards: List[Dict]) -> List[Dict[str, str]]:
    """
    Kombiniert Karteikarten von beiden APIs und entfernt Duplikate.
    
    Priorisiert längere/detailliertere Antworten bei ähnlichen Fragen.
    """
    combined = {}
    
    def normalize_question(q: str) -> str:
        """Normalisiert Frage für Duplikaterkennung."""
        return re.sub(r'[^\w\s]', '', q.lower()).strip()
    
    def score_card(card: Dict) -> int:
        """Bewertet Qualität einer Karte basierend auf Detailtiefe."""
        answer = card.get("antwort", "")
        score = len(answer)  # Längere Antworten = mehr Details
        score += answer.count("\n") * 10  # Strukturierte Antworten
        score += answer.count("Beispiel") * 20  # Mit Beispielen
        score += answer.count(":") * 5  # Erklärungen
        score += answer.count("=") * 15  # Formeln/Rechnungen
        score += answer.count("Formel") * 25  # Formeln erwähnt
        return score
    
    # Alle Karten verarbeiten
    for card in openai_cards + gemini_cards:
        key = normalize_question(card.get("frage", ""))
        if not key:
            continue
        
        # Behalte die bessere Version bei Duplikaten
        if key in combined:
            if score_card(card) > score_card(combined[key]):
                combined[key] = card
        else:
            combined[key] = card
    
    return list(combined.values())


if __name__ == "__main__":
    # Test
    print("Teste LLM Clients...")
    
    try:
        openai_client = OpenAIClient()
        print(f"✓ OpenAI Client initialisiert (Modell: {openai_client.model})")
    except ValueError as e:
        print(f"✗ OpenAI: {e}")
    
    try:
        gemini_client = GeminiClient()
        print("✓ Gemini Client initialisiert (Modell: gemini-2.0-pro)")
    except ValueError as e:
        print(f"✗ Gemini: {e}")
