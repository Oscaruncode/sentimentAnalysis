import asyncio
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
BATCH_SIZE = 10  # Ajusta según tu preferencia

app = FastAPI(title="Sentiment Analysis API")


def build_prompt(responses_batch: list) -> str:
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
{json.dumps([resp.dict() for resp in responses_batch], ensure_ascii=False, indent=2)}
"""
    return prompt.strip()


async def call_ollama(prompt: str, batch_index: int, batch_size: int) -> str:
    print(f"\n➡️ Enviando batch {batch_index} con {batch_size} respuestas al modelo...")
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=260.0) as client:
        response = await client.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        )
    elapsed = time.perf_counter() - start
    print(f"✅ Batch {batch_index} respondido en {elapsed:.2f} segundos")
    print(f"📏 Tamaño de la respuesta: {len(response.text)} caracteres")
    response.raise_for_status()
    data = response.json()
    return data.get("response", "").strip()


@app.post("/SentimentAnalize", response_model=List[SentimentOutput])
async def analyze_sentiments(payload: AnalysisRequest):
    start_total = time.perf_counter()

    # Dividir en batches
    batches = [
        payload.responses[i:i + BATCH_SIZE]
        for i in range(0, len(payload.responses), BATCH_SIZE)
    ]
    print(f"\n📊 Total de respuestas: {len(payload.responses)}")
    print(f"📦 Total de batches: {len(batches)}, tamaño por batch: {BATCH_SIZE}\n")

    # Crear tasks con info de batch
    tasks = [
        call_ollama(build_prompt(batch), batch_index=i + 1, batch_size=len(batch))
        for i, batch in enumerate(batches)
    ]

    # Ejecutar todas las llamadas en paralelo
    raw_outputs = await asyncio.gather(*tasks)

    # Parsear CSV de cada batch
    results = []
    for i, raw_output in enumerate(raw_outputs):
        print(f"\n🔍 Procesando CSV del batch {i + 1}...")
        try:
            f = StringIO(raw_output)
            reader = csv.DictReader(f)
            batch_results = [
                SentimentOutput(AnswerID=row["AnswerID"], Sentiment=int(row["Sentiment"]))
                for row in reader
            ]
            results.extend(batch_results)
            print(f"✅ Batch {i + 1} procesado, respuestas parseadas: {len(batch_results)}")
        except Exception as e:
            raise ValueError(f"Error procesando la salida CSV del batch {i + 1}:\n{raw_output}\n{e}")

    elapsed_total = time.perf_counter() - start_total
    print(f"\n⏱️ Tiempo total de análisis de {len(payload.responses)} respuestas: {elapsed_total:.2f} segundos")
    return results
