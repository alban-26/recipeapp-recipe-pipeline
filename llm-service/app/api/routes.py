from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ocr_client import fetch_ocr_text
from app.services.recipe_service import process_recipe

import time
import structlog

log = structlog.get_logger()

router = APIRouter()


@router.post("/extract")
async def extract_recipe(file: UploadFile = File(...)):
    start_total = time.perf_counter()

    image_bytes = await file.read()

    try:
        start_ocr = time.perf_counter()

        ocr_text = await fetch_ocr_text(
            image_bytes,
            file.filename or "image.jpg"
        )

        ocr_time = time.perf_counter() - start_ocr

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"OCR service error: {exc}"
        )

    if not ocr_text.strip():
        raise HTTPException(
            status_code=422,
            detail="OCR returned no text"
        )

    try:
        start_llm = time.perf_counter()

        recipe = await process_recipe(ocr_text)

        llm_time = time.perf_counter() - start_llm

    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"LLM service error: {exc}"
        )

    total_time = time.perf_counter() - start_total

    log.info(
        "pipeline_timing",
        filename=file.filename,
        ocr_seconds=round(ocr_time, 2),
        llm_seconds=round(llm_time, 2),
        total_seconds=round(total_time, 2),
        ocr_chars=len(ocr_text),
    )

    return recipe.model_dump()