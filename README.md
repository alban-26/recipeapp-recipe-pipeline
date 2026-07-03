# Recipe Pipeline

```
Bild
  ↓
PaddleOCR  (ocr-service  · Port 8080)
  ↓
OCR Text
  ↓
Qwen2.5-0.5B via Ollama  (ollama · Port 11434)
  ↓
JSON Output
  ↓
Pydantic Validation  (llm-service · Port 8081)
  ↓
API Response
```

## Services

| Service       | Port  | Aufgabe                              |
|---------------|-------|--------------------------------------|
| `ocr-service` | 8080  | PaddleOCR – extrahiert Text aus Bild |
| `ollama`      | 11434 | Qwen2.5:0.5b – strukturiert den Text |
| `llm-service` | 8081  | Orchestrierung + Pydantic-Validierung|

## Start

```bash
# 1. Alle Services bauen & starten
docker compose up --build

# 2. Qwen-Modell einmalig herunterladen (nur beim ersten Start nötig)
docker exec recipe-ollama ollama pull qwen2.5:0.5b
```

## Nutzung

```bash
# Rezeptbild einschicken → vollständige Pipeline
curl -X POST http://localhost:8081/api/v1/recipes/extract \
     -F "file=@rezept.jpg"
```

### Beispiel-Response

```json
{
  "title": "Apfelkuchen",
  "servings": 8,
  "ingredients": [
    {"amount": "200", "unit": "g", "name": "Mehl"},
    {"amount": "3",   "unit": null, "name": "Eier"}
  ],
  "steps": [
    "Mehl und Eier vermengen.",
    "Bei 180°C 40 Minuten backen."
  ]
}
```

## Health Checks

```bash
curl http://localhost:8080/health   # OCR Service
curl http://localhost:8081/health   # LLM Service
```

## Projektstruktur

```
recipe-pipeline/
├── docker-compose.yml          ← startet alle 3 Services
├── ocr-service/                ← PaddleOCR (unverändert aus Produktion)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       └── ocr.py
└── llm-service/                ← Orchestrierung + LLM + Validierung
    ├── Dockerfile
    ├── requirements.txt
    └── app/
        ├── main.py
        ├── api/routes.py
        ├── models/recipe.py
        └── services/
            ├── ocr_client.py   ← ruft ocr-service per HTTP auf
            ├── llm_service.py  ← ruft Ollama auf
            └── recipe_service.py ← Pydantic-Validierung
```
