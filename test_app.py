from unittest.mock import patch, MagicMock
import json
from app import buscar_web


def test_buscar_web_parsea_resultados_correctamente():
    respuesta_simulada = {
        "organic": [
            {
                "title": "Resultado de prueba",
                "snippet": "Este es un snippet de prueba",
                "link": "https://ejemplo.com"
            }
        ]
    }

    with patch("app.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = respuesta_simulada
        mock_post.return_value = mock_response

        resultado = buscar_web("consulta de prueba")
        resultado_parseado = json.loads(resultado)

        assert len(resultado_parseado) == 1
        assert resultado_parseado[0]["titulo"] == "Resultado de prueba"
        assert resultado_parseado[0]["snippet"] == "Este es un snippet de prueba"
        assert resultado_parseado[0]["url"] == "https://ejemplo.com"


def test_buscar_web_limita_a_5_resultados():
    respuesta_simulada = {
        "organic": [{"title": f"Resultado {i}", "snippet": "texto", "link": "url"} for i in range(10)]
    }

    with patch("app.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = respuesta_simulada
        mock_post.return_value = mock_response

        resultado = buscar_web("consulta")
        resultado_parseado = json.loads(resultado)

        assert len(resultado_parseado) == 5


def test_buscar_web_maneja_respuesta_vacia():
    with patch("app.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        resultado = buscar_web("consulta sin resultados")
        resultado_parseado = json.loads(resultado)

        assert resultado_parseado == []


def test_buscar_web_maneja_error_de_conexion():
    with patch("app.requests.post") as mock_post:
        mock_post.side_effect = Exception("Connection timeout")

        resultado = buscar_web("consulta")

        assert "Error en búsqueda" in resultado