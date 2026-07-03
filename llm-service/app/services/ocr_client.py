import httpx
import structlog

log = structlog.get_logger()

OCR_SERVICE_URL = "http://ocr-service:8080/api/v1/recipes/extract"


async def fetch_ocr_text(image_bytes: bytes, filename: str) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            OCR_SERVICE_URL,
            files={"file": (filename, image_bytes, "image/jpeg")},
        )
        response.raise_for_status()

    raw = response.json()
    text = raw.get("text", "")
    log.info("ocr_done", chars=len(text), lines=len(raw.get("lines", [])))
    return text