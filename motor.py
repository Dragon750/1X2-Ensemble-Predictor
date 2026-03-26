"""Lógica central para validar, combinar y evaluar predicciones 1X2."""

import json
import os
import sqlite3
import datetime
from pydantic import BaseModel, ValidationError, Field
from typing import Dict, Union

# ==========================================
# ESQUEMAS DE VALIDACIÓN (PYDANTIC)
# ==========================================
class PartidoSchema(BaseModel):
    # Obligatorio. Acepta tanto el número 1 como el texto "1"
    id_partido: Union[int, str]

    # Añade esta línea para que Pydantic acepte y guarde la liga
    liga: str = Field(..., min_length=1, pattern=r'\S') 
    
    # Field(..., min_length=1) significa:
    # "..." -> El campo es estrictamente obligatorio (no puede faltar).
    # "min_length=1" -> No puede ser un texto vacío "".
    # "pattern=r'\S'" -> Impide que alguien ponga solo espacios en blanco "   ".
    local: str = Field(..., min_length=1, pattern=r'\S')
    visitante: str = Field(..., min_length=1, pattern=r'\S')
    
    # min_length=1 asegura que el diccionario no esté vacío {}.
    # Es decir, exige que haya al menos una fuente con sus cuotas.
    predicciones: Dict[str, Dict[str, float]] = Field(..., min_length=1)

# ==========================================
# CONFIGURACIÓN DE ARCHIVOS Y MODELO
# ==========================================
CARPETA_DATOS = "data"
ARCHIVO_SQLITE = os.path.join(CARPETA_DATOS, "database.db") 
ARCHIVO_ENTRADA = os.path.join(CARPETA_DATOS,"jornada.json")
ARCHIVO_RESULTADOS = os.path.join(CARPETA_DATOS,"resultados.json")
ARCHIVO_NOMBRES = os.path.join(CARPETA_DATOS, "nombres_fuentes.json") 
GAMMA_DECAY = 0.95

def cargar_nombres_fuentes():
    """Carga el diccionario secreto de nombres si existe, si no, devuelve uno vacío."""
    if os.path.exists(ARCHIVO_NOMBRES):
        try:
            with open(ARCHIVO_NOMBRES, 'r', encoding='utf-8') as archivo:
                return json.load(archivo)
        except json.JSONDecodeError:
            print("⚠️ Error: Formato incorrecto en nombres_fuentes.json")
    return {}

NOMBRES_FUENTES = cargar_nombres_fuentes()

# ==========================================
# 1. GESTIÓN DE ARCHIVOS
# ==========================================
def cargar_db(ruta_db=ARCHIVO_SQLITE):
    """Lee la tabla `fuentes` y la transforma al diccionario por liga."""
    if not os.path.exists(ruta_db):
        print("Error: Base de datos SQLite no encontrada. Ejecuta set_up_db.py primero.")
        return {}

    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()
    cursor.execute("SELECT id_fuente, liga, nombre, aciertos, total_predicciones FROM fuentes")
    filas = cursor.fetchall()
    conexion.close()

    db_fuentes = {}
    for fila in filas:
        id_f, liga, nombre, aciertos, total = fila
        if liga not in db_fuentes:
            db_fuentes[liga] = {}
            
        db_fuentes[liga][id_f] = {
            "nombre": nombre,
            "aciertos": aciertos,
            "total_predicciones": total
        }
    return db_fuentes

def guardar_db(db_fuentes, ruta_db=ARCHIVO_SQLITE):
    """Persiste las métricas de cada fuente manteniendo su liga."""
    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()

    for liga, fuentes_liga in db_fuentes.items():
        for id_f, datos in fuentes_liga.items():
            nombre_real = NOMBRES_FUENTES.get(id_f, datos.get('nombre', id_f))
            
            cursor.execute('''
                INSERT OR REPLACE INTO fuentes (id_fuente, liga, nombre, aciertos, total_predicciones)
                VALUES (?, ?, ?, ?, ?)
            ''', (id_f, liga, nombre_real, datos['aciertos'], datos['total_predicciones']))

    conexion.commit()
    conexion.close()

def cargar_jornada(ruta_entrada=ARCHIVO_ENTRADA):
    """Lee y valida estrictamente los datos de la semana usando Pydantic."""
    if not os.path.exists(ruta_entrada):
        print(f"Error: No se encuentra el archivo '{ruta_entrada}'.")
        return None
    
    with open(ruta_entrada, 'r', encoding='utf-8') as archivo:
        try:
            jornada_cruda = json.load(archivo)
            
            jornada_validada = []
            for partido in jornada_cruda:
                partido_seguro = PartidoSchema(**partido)
                jornada_validada.append(partido_seguro.model_dump())
                
            print(f"✅ Se han cargado y validado {len(jornada_validada)} partidos desde '{ruta_entrada}'.")
            return jornada_validada
            
        except json.JSONDecodeError:
            print(f"❌ Error crítico de formato en '{ruta_entrada}'. Falta alguna coma o comilla.")
            return None
                    
        except ValidationError as e:
            print(f"\n❌ Pydantic ha bloqueado la carga. Errores detectados en '{ruta_entrada}':")
            
            for idx, error in enumerate(e.errors()):
                if isinstance(error['loc'][0], int):
                    num_partido = error['loc'][0] + 1 
                    nombre_campo = " -> ".join(str(x) for x in error['loc'][1:])
                    ubicacion = f"Partido {num_partido}, campo [{nombre_campo}]"
                else:
                    ubicacion = f"Campo [{" -> ".join(str(x) for x in error['loc'])}]"

                tipo_error = error['type']
                
                if tipo_error == 'missing':
                    mensaje = "Falta este campo por completo. Debes añadirlo en el JSON."
                elif tipo_error in ['string_too_short', 'string_pattern_mismatch']:
                    mensaje = "El campo está vacío o solo tiene espacios. Escribe un texto válido (ej. 'Real Madrid')."
                elif tipo_error == 'dict_too_short':
                    mensaje = "El diccionario de predicciones está vacío. Añade al menos una fuente (ej. 'F1': {'1': 2.0, ...})."
                elif 'type' in tipo_error or 'float' in tipo_error or 'int' in tipo_error:
                    mensaje = "El formato es incorrecto."
                else:
                    mensaje = error['msg'] 

                print(f"\nError {idx + 1} en {ubicacion}")
                print(f"Motivo: {mensaje}")
                
            print("\n💡 Por favor, corrige estos fallos en tu archivo JSON y vuelve a ejecutar el programa.\n")
            return None

def cargar_resultados(ruta_resultados=ARCHIVO_RESULTADOS):
    """Carga resultados reales de la jornada para actualizar estadísticas."""
    if not os.path.exists(ruta_resultados):
        print(f"Error: No se encuentra el archivo '{ruta_resultados}'.")
        return None
    with open(ruta_resultados, 'r', encoding='utf-8') as archivo:
        try:
            return json.load(archivo)
        except json.JSONDecodeError:
            print(f"Error de formato en '{ruta_resultados}'.")
            return None

# ==========================================
# 2. LÓGICA MATEMÁTICA Y ACTUALIZACIÓN
# ==========================================
def obtener_tasa_acierto(datos_fuente):
    """Devuelve la fiabilidad histórica de una fuente en una liga."""
    if datos_fuente['total_predicciones'] == 0:
        return 1.0/3.0
    return datos_fuente['aciertos'] / datos_fuente['total_predicciones']

def limpiar_prediccion(diccionario_valores):
    """Normaliza cuotas o probabilidades para que sumen 1."""
    if any(v > 1 for v in diccionario_valores.values()):
        probs_implicitas = {k: (1 / v) for k, v in diccionario_valores.items()}
        suma_implicitas = sum(probs_implicitas.values())
        return {k: (v / suma_implicitas) for k, v in probs_implicitas.items()}
    else:
        suma = sum(diccionario_valores.values())
        return {k: (v / suma) for k, v in diccionario_valores.items()}

def calcular_jornada(jornada, db_fuentes):
    """Combina predicciones de varias fuentes usando pesos por rendimiento."""
    resultados_jornada = []
    
    for partido in jornada:
        if 'liga' not in partido or not partido['liga'].strip():
            local = partido.get('local', 'Desconocido')
            visitante = partido.get('visitante', 'Desconocido')
            print(f"\n❌ ERROR CRÍTICO: El partido '{local} vs {visitante}' no tiene una liga asignada.")
            print("⚠️ Ejecución cancelada. Añade el campo 'liga' en data/jornada.json y vuelve a intentarlo.\n")
            exit(1)
            
        liga = partido['liga']
        prob_finales = {'1': 0.0, 'X': 0.0, '2': 0.0}
        
        # Peso de cada fuente en este partido según su histórico en la misma liga.
        tasas_partido = {}
        for id_fuente in partido['predicciones']:
            if liga in db_fuentes and id_fuente in db_fuentes[liga]:
                tasas_partido[id_fuente] = obtener_tasa_acierto(db_fuentes[liga][id_fuente])
            else:
                tasas_partido[id_fuente] = 1.0 / 3.0

        suma_tasas = sum(tasas_partido.values())
        
        for id_fuente, probs_brutas in partido['predicciones'].items():
            probs_limpias = limpiar_prediccion(probs_brutas)
            tasa = tasas_partido[id_fuente]
            peso = tasa / suma_tasas if suma_tasas > 0 else (1.0 / len(partido['predicciones']))
            
            prob_finales['1'] += peso * probs_limpias['1']
            prob_finales['X'] += peso * probs_limpias['X']
            prob_finales['2'] += peso * probs_limpias['2']
        
        resultados_jornada.append({
            "liga": liga,
            "partido": f"{partido['local']} vs {partido['visitante']}",
            "probabilidades": prob_finales
        })
        
    return resultados_jornada

def actualizar_estadisticas(jornada, resultados_reales, db_fuentes):
    """Actualiza score histórico de las fuentes con decaimiento temporal."""
    # El decaimiento evita que resultados muy antiguos dominen el ranking actual.
    for liga in db_fuentes:
        for id_fuente in db_fuentes[liga]:
            db_fuentes[liga][id_fuente]['aciertos'] *= GAMMA_DECAY
            db_fuentes[liga][id_fuente]['total_predicciones'] *= GAMMA_DECAY

    for partido in jornada:
        id_p = str(partido['id_partido'])
        if id_p not in resultados_reales or resultados_reales[id_p] == "?":
            continue
            
        if 'liga' not in partido or not partido['liga'].strip():
            print(f"\n❌ ERROR CRÍTICO al actualizar: Un partido (ID {id_p}) no tiene liga asignada.")
            exit(1)
            
        resultado_real = resultados_reales[id_p]
        liga = partido['liga']
        
        if liga not in db_fuentes:
            db_fuentes[liga] = {}
        
        for id_fuente, probs_brutas in partido['predicciones'].items():
            if id_fuente not in db_fuentes[liga]:
                nombre_real = NOMBRES_FUENTES.get(id_fuente, id_fuente)
                db_fuentes[liga][id_fuente] = {"nombre": nombre_real, "aciertos": 0.0, "total_predicciones": 0.0}
                
            db_fuentes[liga][id_fuente]['total_predicciones'] += 1
            probs_limpias = limpiar_prediccion(probs_brutas)
            
            # Brier score multi-clase convertido a puntuación [0, 1].
            brier_sum = 0.0
            for opcion in ['1', 'X', '2']:
                prob_real = 1.0 if opcion == resultado_real else 0.0
                prob_predicha = probs_limpias.get(opcion, 0.0)
                brier_sum += (prob_predicha - prob_real) ** 2
            
            puntuacion = 1 - (brier_sum / 2)
            db_fuentes[liga][id_fuente]['aciertos'] += puntuacion
                
    return db_fuentes

def guardar_historial_jornada(jornada, resultados_reales, ruta_db=ARCHIVO_SQLITE):
    """Guarda en SQLite los partidos cerrados y predicciones normalizadas."""
    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()
    fecha_actual = datetime.datetime.now().strftime("%Y%m%d")

    for partido in jornada:
        id_temporal = str(partido['id_partido']) 
        if id_temporal not in resultados_reales or resultados_reales[id_temporal] == "?":
            continue
            
        if 'liga' not in partido or not partido['liga'].strip():
            conexion.close()
            exit(1)
            
        resultado = resultados_reales[id_temporal]
        liga = partido['liga']
        
        local_limpio = partido['local'].replace(" ", "")
        visitante_limpio = partido['visitante'].replace(" ", "")
        id_db = f"{local_limpio}_{visitante_limpio}_{fecha_actual}"
        
        cursor.execute('''
            INSERT OR IGNORE INTO partidos (id_partido, liga, local, visitante, resultado_real)
            VALUES (?, ?, ?, ?, ?)
        ''', (id_db, liga, partido['local'], partido['visitante'], resultado))
        
        for id_fuente, probs_brutas in partido['predicciones'].items():
            probs_limpias = limpiar_prediccion(probs_brutas)
            cursor.execute('''
                INSERT OR REPLACE INTO predicciones (id_partido, id_fuente, prob_1, prob_X, prob_2)
                VALUES (?, ?, ?, ?, ?)
            ''', (id_db, id_fuente, probs_limpias['1'], probs_limpias['X'], probs_limpias['2']))

    conexion.commit()
    conexion.close()