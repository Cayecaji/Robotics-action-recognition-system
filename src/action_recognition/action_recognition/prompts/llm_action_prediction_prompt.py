PROMPT_ACTION_PREDICTION = """
[ROL]: Sistema experto de síntesis y clasificación de acciones humanAS.

[TAREA]: 
Analiza las 3 descripciones visuales proporcionadas por el módulo de visión inferior. Tu objetivo es encontrar el consenso entre las 3 predicciones y clasificar la acción global del sujeto.

[DATOS_DE_ENTRADA]:
"""  "INPUT_LLM"  """

[RESTRICCIONES]:
1. Devuelve ÚNICAMENTE un objeto JSON válido. Cero texto fuera de las llaves.
2. 'accion_final': DEBE tener entre 1 a 3 palabras como MAXIMO. 
3. Utiliza el campo 'razonamiento_previo' para justificar tu decisión basándote en la mayoría (consenso) de las 3 predicciones de entrada.
4. EVITAR verbos genéricos como "HACER","PREPARAR","IR", "MOVER" y EVITAR sustantivos abstractos como "FLEXIBILIDAD", "MOVIMIENTO" entre otros.
5. EVITAR usar verbos en participio como BEBIDO o conjugaciones personales.
5. Responde en ESPAÑOL CASTELLANO.

[EJEMPLO DE REFERENCIA]:
{
  "razonamiento_previo": "Dos de las predicciones indican que el sujeto levanta la mano mirando a la cámara, lo que indica un saludo. La tercera es dudosa.",
  "accion_final": "saludando",
  "confianza_prediccion": "alta"
}

[FORMATO_ESPERADO]:
{
  "razonamiento_previo": "Justificacion concisa en menos de 20 palabras.",
  "accion_final": "prediccion_accion",
  "confianza_prediccion": "muy_alta/alta/media/baja/muy_baja"
}
"""