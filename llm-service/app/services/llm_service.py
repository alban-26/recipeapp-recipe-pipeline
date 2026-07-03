import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_fixed

log = structlog.get_logger()

OLLAMA_URL = "http://ollama:11434/api/generate"
MODEL = "qwen2.5:0.5b"

SYSTEM_PROMPT = """
Du bist ein Parser für Kochrezepte.

Extrahiere aus dem OCR-Text genau ein Rezept.

Antworte ausschließlich mit gültigem JSON.
Keine Markdown-Blöcke.
Keine Erklärungen.
Keine Kommentare.
Kein zusätzlicher Text.

Das JSON muss exakt dieses Schema besitzen:

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

- "name" ist der Rezeptname.
- "portions" ist die Anzahl der Portionen als Integer.
- "duration" ist die gesamte Kochzeit in Minuten.
- "quantity" enthält ausschließlich die Zahl.
- "unit" enthält ausschließlich die Einheit (g, kg, ml, EL, TL, Stück usw.).
- "name" enthält ausschließlich den Namen der Zutat.
- Falls quantity, unit, portions oder duration nicht vorhanden sind, verwende null.
- "instructions" enthält jeden Kochschritt als einzelnen Listeneintrag.
- Gib niemals zusätzliche Felder zurück.
"""


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def call_llm(ocr_text: str) -> str:
    """
    Sends OCR text to Ollama and returns the generated JSON string.
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
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0,
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