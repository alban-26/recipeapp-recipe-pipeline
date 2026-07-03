import os
import cv2
import numpy as np
import hashlib

from fastapi import FastAPI, UploadFile, File
from cachetools import TTLCache
from rapidocr_onnxruntime import RapidOCR

MAX_WIDTH = 1600

app = FastAPI(title="Recipe OCR Service")

ocr = RapidOCR()

cache = TTLCache(
    maxsize=1000,
    ttl=3600,
)


def preprocess_image(image_bytes: bytes):
    img_array = np.frombuffer(image_bytes, np.uint8)

    img = cv2.imdecode(
        img_array,
        cv2.IMREAD_COLOR,
    )

    if img is None:
        raise ValueError("Invalid image")

    h, w = img.shape[:2]

    if w > MAX_WIDTH:
        scale = MAX_WIDTH / w

        img = cv2.resize(
            img,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_AREA,
        )

    return img


def hash_image(image_bytes: bytes) -> str:
    return hashlib.md5(image_bytes).hexdigest()


def run_ocr(img) -> list[str]:
    result, _ = ocr(img)

    lines: list[str] = []

    if result:
        for line in result:
            text = line[1]
            score = line[2]

            if score > 0.5 and text.strip():
                lines.append(text.strip())

    return lines


@app.post("/api/v1/recipes/extract")
async def extract_recipe(file: UploadFile = File(...)):
    image_bytes = await file.read()

    cache_key = hash_image(image_bytes)

    if cache_key in cache:
        lines = cache[cache_key]

        return {
            "cached": True,
            "text": "\n".join(lines),
            "lines": lines,
        }

    img = preprocess_image(image_bytes)

    lines = run_ocr(img)

    cache[cache_key] = lines

    return {
        "cached": False,
        "text": "\n".join(lines),
        "lines": lines,
    }


@app.get("/health")
async def health():
    return {"status": "ok"}