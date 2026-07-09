import anthropic
import requests
import os
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
cliente = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

tools = [
    {
        "name": "buscar_web",
        "description": "Busca información actualizada en internet sobre cualquier tema",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "La búsqueda a realizar en internet"
                }
            },
            "required": ["query"]
        }
    }
]

def buscar_web(query):
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    body = {"q": query, "num": 5, "gl": "ec", "hl": "es"}
    
    try:
        res = requests.post(url, headers=headers, json=body)
        data = res.json()
        resultados = []
        for r in data.get("organic", [])[:5]:
            resultados.append({
                "titulo": r.get("title", ""),
                "snippet": r.get("snippet", ""),
                "url": r.get("link", "")
            })
        return json.dumps(resultados, ensure_ascii=False)
    except Exception as e:
        return f"Error en búsqueda: {str(e)}"

def ejecutar_agente(pregunta):
    messages = [{"role": "user", "content": pregunta}]
    
    respuesta = cliente.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system="""Eres un asistente inteligente con acceso a internet.
Cuando necesites información actualizada, usa la herramienta buscar_web.
Responde siempre en español de forma clara y concisa.
Cita las fuentes cuando uses información de internet.""",
        tools=tools,
        messages=messages
    )
    
    while respuesta.stop_reason == "tool_use":
        tool_use = next(b for b in respuesta.content if b.type == "tool_use")
        query = tool_use.input["query"]
        
        print(f"[Buscando: {query}]")
        resultado = buscar_web(query)
        
        messages.append({"role": "assistant", "content": respuesta.content})
        messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": resultado
            }]
        })
        
        respuesta = cliente.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system="""Eres un asistente inteligente con acceso a internet.
Cuando necesites información actualizada, usa la herramienta buscar_web.
Responde siempre en español de forma clara y concisa.
Cita las fuentes cuando uses información de internet.""",
            tools=tools,
            messages=messages
        )
    
    return respuesta.content[0].text

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    pregunta = data.get("mensaje", "")
    respuesta = ejecutar_agente(pregunta)
    return jsonify({"respuesta": respuesta})

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)