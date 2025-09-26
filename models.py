from typing import Dict, List
from pydantic import BaseModel

# Entrada
class ResponseInput(BaseModel):
    AnswerID: int
    QuestionId: int
    AnswerText: str

# Salida
class SentimentOutput(BaseModel):
    AnswerID: int
    Sentiment: int  # 0 = Negativo, 1 = Positivo, 2 = Neutro

# Payload del request
class AnalysisRequest(BaseModel):
    questions: Dict[int, str]
    responses: List[ResponseInput]
