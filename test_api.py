import requests

url = "http://localhost:8000/SentimentAnalize"

payload = {
  "questions": {
    "1": "¿Cómo percibes el ambiente laboral?",
    "2": "¿Recibes apoyo de tu equipo?",
    "3": "¿Qué opinas de tu carga laboral?",
    "4": "¿Cómo describirías la comunicación con tus jefes?",
    "5": "¿Qué piensas de las oportunidades de crecimiento?"
  },
  "responses": [
    { "AnswerID": 1, "QuestionId": 1, "AnswerText": "El ambiente es excelente, me siento motivado" },
    { "AnswerID": 2, "QuestionId": 1, "AnswerText": "El ambiente es malo, mucha tensión entre compañeros" },
    { "AnswerID": 3, "QuestionId": 1, "AnswerText": "El ambiente es regular, a veces bien, a veces mal" },
    { "AnswerID": 4, "QuestionId": 2, "AnswerText": "Mi equipo siempre me apoya y colabora" },
    { "AnswerID": 5, "QuestionId": 2, "AnswerText": "Nunca recibo ayuda, cada uno se preocupa solo por sí mismo" },
    { "AnswerID": 6, "QuestionId": 2, "AnswerText": "A veces recibo apoyo, otras no, depende del día" },
    { "AnswerID": 7, "QuestionId": 3, "AnswerText": "La carga laboral es excesiva e inhumana" },
    { "AnswerID": 8, "QuestionId": 3, "AnswerText": "Tengo una carga laboral adecuada y balanceada" },
    { "AnswerID": 9, "QuestionId": 3, "AnswerText": "La carga es alta pero manejable" },
    { "AnswerID": 10, "QuestionId": 4, "AnswerText": "Mis jefes son claros y escuchan mis inquietudes" },
    { "AnswerID": 11, "QuestionId": 4, "AnswerText": "Mis jefes nunca escuchan y la comunicación es pésima" },
    { "AnswerID": 12, "QuestionId": 4, "AnswerText": "La comunicación es aceptable, aunque podría mejorar" },
    { "AnswerID": 13, "QuestionId": 5, "AnswerText": "Tengo oportunidades de ascenso y capacitación" },
    { "AnswerID": 14, "QuestionId": 5, "AnswerText": "Aquí no hay futuro, todo está estancado" },
    { "AnswerID": 15, "QuestionId": 5, "AnswerText": "No lo sé, no tengo mucha información" },
    { "AnswerID": 16, "QuestionId": 1, "AnswerText": "El ambiente es cálido y de confianza" },
    { "AnswerID": 17, "QuestionId": 1, "AnswerText": "El ambiente es muy tóxico" },
    { "AnswerID": 18, "QuestionId": 1, "AnswerText": "Es un ambiente indiferente, nada especial" },
    { "AnswerID": 19, "QuestionId": 2, "AnswerText": "Siempre que necesito algo, mi equipo me respalda" },
    { "AnswerID": 20, "QuestionId": 2, "AnswerText": "Mi equipo nunca está disponible" },
    { "AnswerID": 21, "QuestionId": 2, "AnswerText": "Algunas veces sí, otras veces no" },
    { "AnswerID": 22, "QuestionId": 3, "AnswerText": "La carga es justa y me permite conciliar con mi vida personal" }
  ]
}


headers = {"Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)

print("Status code:", response.status_code)
print("Response JSON:", response.json())
