from fastapi import FastAPI
from typing import List
import httpx
import json
import time
import csv
from io import StringIO

from models import AnalysisRequest, SentimentOutput

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

app = FastAPI(title="Sentiment Analysis API")

def build_prompt(payload: AnalysisRequest) -> str:
    prompt = f"""
Eres un analista experto en encuestas de clima laboral.
Tu única tarea es clasificar cada respuesta en un valor numérico de sentimiento.
No expliques, no agregues texto extra, no agregues comentarios: devuelve únicamente CSV válido.

Criterios de clasificación:
0 = Negativo
1 = Positivo
2 = Neutro

Reglas:
- No inventes, elimines ni dupliques ningún AnswerID.
- Mantén el orden de las respuestas tal como aparecen.
- Si no está claro cuál predomina, usa 2 = Neutro.
- La salida debe ser CSV con encabezados: AnswerID,Sentiment

ANALIZA EL SIGUIENTE JSON:
{json.dumps([resp.dict() for resp in payload.responses], ensure_ascii=False, indent=2)}
"""
    return prompt.strip()



async def call_ollama(prompt: str) -> str:
    print(prompt)
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=260.0) as client:
        response = await client.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        )
    elapsed = time.perf_counter() - start
    print(f"⏱️ Ollama respondió en {elapsed:.2f} segundos")

    response.raise_for_status()
    data = response.json()
    return data.get("response", "").strip()


@app.post("/SentimentAnalize", response_model=List[SentimentOutput])
async def analyze_sentiments(payload: AnalysisRequest):
    start = time.perf_counter()

    prompt = build_prompt(payload)
    raw_output = await call_ollama(prompt)

    try:
        f = StringIO(raw_output)
        reader = csv.DictReader(f)
        results = [
            SentimentOutput(AnswerID=row["AnswerID"], Sentiment=int(row["Sentiment"]))
            for row in reader
        ]
    except Exception as e:
        raise ValueError(f"Error procesando la salida CSV: {raw_output}\n{e}")

    elapsed = time.perf_counter() - start
    print(f"⏱️ Tiempo total de análisis: {elapsed:.2f} segundos")

    return results