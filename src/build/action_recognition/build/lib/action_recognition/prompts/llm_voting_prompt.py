PROMPT_VOTING = """
[ROL]: Sistema de resolución de consenso y agrupación semántica.

[TAREA]: 
Analiza las 5 predicciones de acción proporcionadas. Tu objetivo es encontrar la acción mayoritaria agrupando aquellas que signifiquen lo mismo, aunque estén escritas de forma distinta.

[DATOS_DE_ENTRADA]: \n
""" "INPUT_VOTING" """

[RESTRICCIONES CRÍTICAS]:
1. RESPUESTA ESTRICTA EN JSON.
2. Agrupa variaciones semánticas (ej: "Beber", "Bebiendo", "Tomando bebida" cuentan todas para el mismo concepto).
3. El campo 'accion_final' DEBE ser el verbo en infinitivo de la acción ganadora (ej: "beber", "caminar", "saludar").

[FORMATO_ESPERADO]:
{
"accion_final": "Nombre de la acción predominante",
"conteo_votos": "X/5",
"justificacion_breve": "Acciones agrupadas: [Lista los grupos semánticamente similares agrupados en “conteo_votos”]"
}
"""