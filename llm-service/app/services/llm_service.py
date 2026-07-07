import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_fixed

log = structlog.get_logger()

OLLAMA_URL = "http://ollama:11434/api/generate"

# Empfehlung:
# qwen2.5:3b oder qwen2.5:7b liefern deutlich stabilere Ergebnisse.
MODEL = "qwen2.5:0.5b"

SYSTEM_PROMPT = """
Du bist ein Parser für Kochrezepte.

Deine Aufgabe:
Extrahiere aus dem OCR-Text genau EIN Rezept.

Antworte ausschließlich mit gültigem JSON.

WICHTIG:

- Keine Markdown-Blöcke.
- Keine Erklärungen.
- Keine Kommentare.
- Kein Text vor dem JSON.
- Kein Text nach dem JSON.
- Das JSON muss direkt mit { beginnen und mit } enden.
- Das JSON muss vollständig parsebar sein.

Das JSON muss EXAKT dieses Schema besitzen:

{
  "name": "string",
  "portions": integer | null,
  "duration": integer | null,
  "ingredients": [
    {
      "quantity": number | null,
      "unit": "string | null",
      "name": "string"
    }
  ],
  "instructions": [
    "string"
  ]
}

Regeln:

- "name" ist ausschließlich der Rezeptname.
- "portions" ist die Anzahl der Portionen als Integer.
- "duration" ist die gesamte Kochzeit in Minuten.
- Falls portions oder duration unbekannt sind, verwende null.

Für Zutaten gilt:

- quantity enthält ausschließlich die Zahl.
- unit enthält ausschließlich eine erlaubte Einheit oder null.
- name enthält ausschließlich den Namen der Zutat.
- Mengen oder Einheiten dürfen niemals im Namen stehen.
- Falls keine Menge vorhanden ist:
  - quantity = null
  - unit = null

Erlaubte Einheiten:

g
kg
mg
µg
lb
oz
ml
l
cl
dl
fl oz
pt
qt
gal
TL
EL
Tasse
Shot
Stück
Scheibe
Blatt
Zehe
Prise
Schuss
Tropfen
Packung
Dose
Glas
Bund
Zweig

Falls eine Einheit nicht exakt einer erlaubten Einheit entspricht:
- unit = null

Beispiele:

"500 g Mehl"

{
  "quantity": 500,
  "unit": "g",
  "name": "Mehl"
}

"2 Eier"

{
  "quantity": 2,
  "unit": "Stück",
  "name": "Ei"
}

"Salz"

{
  "quantity": null,
  "unit": null,
  "name": "Salz"
}

Anweisungen:

- Jeder Kochschritt ist ein eigener Listeneintrag.
- Reihenfolge beibehalten.
- Keine Nummerierung.
- Keine leeren Einträge.

Allgemeine Regeln:

- Fehlende Werte werden mit null angegeben.
- Erfinde niemals Informationen.
- Gib niemals zusätzliche Felder zurück.
"""


JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string"
        },
        "portions": {
            "type": ["integer", "null"]
        },
        "duration": {
            "type": ["integer", "null"]
        },
        "ingredients": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "quantity": {
                        "type": ["number", "null"]
                    },
                    "unit": {
                        "type": ["string", "null"]
                    },
                    "name": {
                        "type": "string"
                    }
                },
                "required": [
                    "quantity",
                    "unit",
                    "name"
                ],
                "additionalProperties": False
            }
        },
        "instructions": {
            "type": "array",
            "items": {
                "type": "string"
            }
        }
    },
    "required": [
        "name",
        "portions",
        "duration",
        "ingredients",
        "instructions"
    ],
    "additionalProperties": False
}


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def call_llm(ocr_text: str) -> str:
    """
    Send OCR text to Ollama and return the extracted recipe JSON.
    """

    prompt = f"""
{SYSTEM_PROMPT}

OCR TEXT:

{ocr_text}

JSON:
"""

    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            OLLAMA_URL,
            json={
                "model": MODEL,

                "system": SYSTEM_PROMPT,

                "prompt": ocr_text,

                "stream": False,

                "format": JSON_SCHEMA,

                "keep_alive": "2h",

                "options": {
                    "temperature": 0,

                    # Geschwindigkeit
                    "num_predict": 500,
                    "num_ctx": 1024,

                    # i5-10210U
                    "num_thread": 4,

                    "top_k": 1,
                    "top_p": 0.1,
                },
            },
        )

        response.raise_for_status()

    result = response.json()["response"]

    log.info(
        "llm_done",
        model=MODEL,
        response_len=len(result),
    )

    return result