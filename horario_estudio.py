# -*- coding: utf-8 -*-
"""Genera un horario de estudio personalizado a partir del silabo y la
ficha de evaluacion de un curso: extrae la estructura (temas por semana,
fechas y pesos de evaluaciones) y, con la fecha de inicio de clases, calcula
el calendario real de fechas. Archivo separado de calendario.py a proposito
(evita chocar con cambios en paralelo)."""
import json
from datetime import timedelta

from tutor_ai import client, MODELO_RESUMEN


def extraer_estructura_curso(texto_silabo, texto_ficha):
    """Le pide a la IA que lea el silabo y la ficha de evaluacion y devuelva
    una estructura clara: cuantas semanas tiene el ciclo, que tema se ve
    cada semana, y en que semana cae cada evaluacion (con su peso y tipo).
    Devuelve un dict, o None si algo fallo."""
    material = f"SILABO:\n{texto_silabo[:4000]}\n\nFICHA DE EVALUACION:\n{texto_ficha[:3000]}"

    prompt = f"""Lee este silabo y ficha de evaluacion de un curso universitario, y extrae
su estructura en JSON. Presta atencion a los numeros de semana exactos que
aparecen en los documentos (no los inventes).

Devuelve SOLO este JSON, sin texto extra:
{{
  "total_semanas": numero total de semanas del ciclo (normalmente 16, usa lo que diga el documento),
  "temas_por_semana": [
    {{"semana": 1, "tema": "nombre corto del tema de esa semana (max 10 palabras)"}}
  ],
  "evaluaciones": [
    {{"semana": numero de semana en que cae, "nombre": "nombre de la evaluacion", "peso_porcentaje": numero (0 si no dice), "tipo": "tipo de evaluacion (examen escrito, video, cuestionario, etc.)"}}
  ]
}}

Incluye TODAS las semanas que tengan tema mencionado, y TODAS las evaluaciones
que encuentres en la ficha (incluyendo las de 0%, como evaluaciones diagnosticas).

Material del curso:
{material}
"""
    try:
        respuesta = client.chat.completions.create(
            model=MODELO_RESUMEN,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1800,
            response_format={"type": "json_object"}
        )
        return json.loads(respuesta.choices[0].message.content)
    except Exception:
        return None


def calcular_horario_con_fechas(estructura, fecha_inicio_ciclo, dias_anticipacion_estudio=5):
    """A partir de la estructura extraida (temas_por_semana, evaluaciones) y
    la fecha real en que empiezan las clases, calcula la fecha exacta de
    cada semana y arma un plan de estudio: para cada evaluacion, sugiere
    desde que fecha empezar a repasar y que temas cubre.

    Asume que cada semana dura 7 dias, empezando en 'fecha_inicio_ciclo'
    (que deberia ser el primer dia de clases, semana 1).

    No usa IA - es puro calculo, asi que el resultado es 100% predecible."""
    temas = {t["semana"]: t["tema"] for t in estructura.get("temas_por_semana", [])}
    evaluaciones = estructura.get("evaluaciones", [])

    def fecha_de_semana(numero_semana):
        # Semana 1 empieza en fecha_inicio_ciclo; cada semana siguiente suma 7 dias
        return fecha_inicio_ciclo + timedelta(weeks=numero_semana - 1)

    plan = []
    semana_anterior_evaluada = 0
    for ev in sorted(evaluaciones, key=lambda e: e["semana"]):
        semana_eval = ev["semana"]
        fecha_eval = fecha_de_semana(semana_eval)
        fecha_inicio_repaso = fecha_eval - timedelta(days=dias_anticipacion_estudio)

        # Temas cubiertos desde la ultima evaluacion hasta esta (los que hay que repasar)
        temas_a_repasar = [
            temas[s] for s in sorted(temas.keys())
            if semana_anterior_evaluada < s <= semana_eval
        ]

        plan.append({
            "evaluacion": ev["nombre"],
            "tipo": ev.get("tipo", ""),
            "peso_porcentaje": ev.get("peso_porcentaje", 0),
            "semana": semana_eval,
            "fecha_evaluacion": fecha_eval,
            "fecha_inicio_repaso": fecha_inicio_repaso,
            "temas_a_repasar": temas_a_repasar,
        })
        semana_anterior_evaluada = semana_eval

    return plan
