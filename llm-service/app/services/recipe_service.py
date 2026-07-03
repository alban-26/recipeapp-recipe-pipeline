import json
import structlog

from app.models.recipe import Recipe
from app.services.llm_service import call_llm

log = structlog.get_logger()


def _strip_fences(text: str) -> str:
    """Remove optional ```json ... ``` markdown fences the LLM might add."""
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(
            lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        )

    return text.strip()


async def process_recipe(ocr_text: str) -> Recipe:
    """
    1. Pass OCR text to Ollama
    2. Parse the returned JSON
    3. Validate with Pydantic
    """

    raw_json = await call_llm(ocr_text)

    raw_json = await call_llm(ocr_text)

    print("========== LLM ==========")
    print(raw_json)
    print("=========================")

    cleaned = _strip_fences(raw_json)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        log.error("json_parse_failed", raw=cleaned[:500])
        raise ValueError(f"LLM returned invalid JSON: {exc}") from exc

    recipe = Recipe.model_validate(data)

    log.info(
        "recipe_validated",
        name=recipe.name,
        ingredients=len(recipe.ingredients),
        instructions=len(recipe.instructions),
    )

    return recipe