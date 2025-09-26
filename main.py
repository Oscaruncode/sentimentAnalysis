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
BATCH_SIZE = 5  # Ajusta según tu preferencia
MAX_RETRIES = 3   # Número máximo de reintentos por batch
RETRY_DELAY = 3   # Segundos a esperar antes de reintentar

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
{json.dumps([resp.dict() for resp in responses_batch], ensure_ascii=False, separators=(',', ':'))}
"""
    return prompt.strip()


async def call_ollama_with_retry(prompt: str, batch_index: int, batch_size: int) -> str:
    """Llama a Ollama con reintentos si falla"""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"\n➡️ Enviando batch {batch_index} (intento {attempt}) con {batch_size} respuestas...")
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
        except Exception as e:
            print(f"⚠️ Error en batch {batch_index} (intento {attempt}): {e}")
            if attempt < MAX_RETRIES:
                print(f"🔁 Reintentando en {RETRY_DELAY} segundos...")
                await asyncio.sleep(RETRY_DELAY)
            else:
                raise RuntimeError(f"❌ Falló batch {batch_index} después de {MAX_RETRIES} intentos.") from e


async def call_and_validate_batch(batch, batch_index: int) -> List[SentimentOutput]:
    """Llama a Ollama y asegura que la salida sea un CSV válido, reintentando si falla.
       Detecta si el CSV viene sin encabezado y lo corrige automáticamente."""
    for attempt in range(1, MAX_RETRIES + 1):
        prompt = build_prompt(batch)
        raw_output = await call_ollama_with_retry(prompt, batch_index, len(batch))

        # Limpiamos líneas vacías
        raw_output = "\n".join([line for line in raw_output.splitlines() if line.strip()])

        try:
            f = StringIO(raw_output)
            reader = csv.reader(f)
            rows = list(reader)

            if not rows:
                raise ValueError("CSV vacío")

            # Detectar si hay encabezados válidos
            first_row = rows[0]
            if first_row == ["AnswerID", "Sentiment"]:
                data_rows = rows[1:]
            elif all(cell.isdigit() for cell in first_row[1:]):  # primera fila sin encabezado
                data_rows = rows
            else:
                # Si los encabezados están mal, asumimos que es una fila de datos
                data_rows = rows

            results = []
            for row in data_rows:
                if len(row) != 2:
                    raise ValueError(f"Fila con formato inválido: {row}")
                answer_id, sentiment_str = row
                if sentiment_str not in {"0", "1", "2"}:
                    raise ValueError(f"Sentiment inválido en AnswerID {answer_id}: {sentiment_str}")
                results.append(SentimentOutput(AnswerID=answer_id, Sentiment=int(sentiment_str)))

            return results

        except Exception as e:
            print(f"⚠️ Validación CSV fallida para batch {batch_index} (intento {attempt}): {e}")
            if attempt < MAX_RETRIES:
                print(f"🔁 Reintentando batch {batch_index} en {RETRY_DELAY} segundos...")
                await asyncio.sleep(RETRY_DELAY)
            else:
                raise RuntimeError(
                    f"❌ Batch {batch_index} falló después de {MAX_RETRIES} intentos.\nÚltima salida:\n{raw_output}"
                ) from e


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

    results = []
    for i, batch in enumerate(batches):
        batch_results = await call_and_validate_batch(batch, batch_index=i + 1)
        results.extend(batch_results)
        print(f"✅ Batch {i + 1} procesado, respuestas parseadas: {len(batch_results)}")

    elapsed_total = time.perf_counter() - start_total
    print(f"\n⏱️ Tiempo total de análisis de {len(payload.responses)} respuestas: {elapsed_total:.2f} segundos")
    return results
