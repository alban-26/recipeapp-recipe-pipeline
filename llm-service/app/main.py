from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Recipe LLM Service")
app.include_router(router, prefix="/api/v1/recipes")


@app.get("/health")
async def health():
    return {"status": "ok"}
