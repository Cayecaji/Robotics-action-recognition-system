PROMPT_SCENE_DESCRIPTION = """
[ROL]: Sistema experto de percepción visual y análisis de secuencias temporales.

[CONTEXTO DE DETECCIÓN]:
A continuación se detalla el conteo de personas y sus identificadores (ID) detectados en una secuencia de 5 frames ordenados cronológicamente:
"""  "INPUT_LVLM"  """

[TAREA]: 
Analiza la progresión temporal de los 5 frames junto con el contexto de IDs proporcionado. Describe la secuencia de acción realizada, centrándote especialmente en los IDs que mantienen consistencia a lo largo de la secuencia.

[RESTRICCIONES]:
1. Devuelve ÚNICAMENTE un objeto JSON válido, sin bloques de código markdown (```json) ni texto introductorio o de despedida.
2. Si hay varios IDs, prioriza la acción del sujeto principal o describe la interacción.
3. El vocabulario para "trayectoria" debe ser estrictamente uno de los siguientes: ["acercandose", "alejandose", "izquierda_a_derecha", "derecha_a_izquierda", "estatico", "indefinido"].


### Salida esperada:
{
  "descripcion_secuencia": "Un sujeto cruza la habitación mientras otro saluda.",
  "sujeto":
    {
      "id_rastreado": "ID_4",
      "trayectoria": "derecha_a_izquierda",
      "confianza": "alta"
    }
}

[FORMATO_ESPERADO]:
{
  "descripcion_secuencia": "Descripción global de la acción en menos de 15 palabras.",
  "sujeto": 
    {
      "id_rastreado": "ID del sujeto (ej. ID_1) o 'Desconocido'",
      "trayectoria": "Valor del vocabulario cerrado",
      "confianza": "alta/media/baja"
    }
}
"""