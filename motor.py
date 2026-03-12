import json
import os

# ==========================================
# CONFIGURACIÓN DE ARCHIVOS Y MODELO
# ==========================================
CARPETA_DATOS = "data"
ARCHIVO_DB = os.path.join(CARPETA_DATOS,"fuentes.json")
ARCHIVO_ENTRADA = os.path.join(CARPETA_DATOS,"jornada.json")
ARCHIVO_RESULTADOS = os.path.join(CARPETA_DATOS,"resultados.json")
GAMMA_DECAY = 0.95

# ==========================================
# 1. GESTIÓN DE ARCHIVOS (LECTURA Y ESCRITURA)
# ==========================================
def cargar_db(ruta_db=ARCHIVO_DB):
    """Carga el diccionario de fuentes desde un archivo JSON."""
    if os.path.exists(ruta_db):
        with open(ruta_db, 'r', encoding='utf-8') as archivo:
            return json.load(archivo)
    else:
        print(f"Aviso: No se ha encontrado la base de datos '{ruta_db}'.")
        print("Asegúrate de haber creado el archivo inicial con tus fuentes.")
        return None

def guardar_db(db_fuentes, ruta_db=ARCHIVO_DB):
    """Sobrescribe el archivo de la base de datos con los datos actualizados."""
    with open(ruta_db, 'w', encoding='utf-8') as archivo:
        json.dump(db_fuentes, archivo, indent=4, ensure_ascii=False)
    print(f"Base de datos guardada con éxito en: {ruta_db}")

def cargar_jornada(ruta_entrada=ARCHIVO_ENTRADA):
    """Lee los datos de los partidos y predicciones de la semana."""
    if not os.path.exists(ruta_entrada):
        print(f"Error: No se encuentra el archivo '{ruta_entrada}'.")
        return None
    
    with open(ruta_entrada, 'r', encoding='utf-8') as archivo:
        try:
            jornada = json.load(archivo)
            print(f"Se han cargado {len(jornada)} partidos desde '{ruta_entrada}'.")
            return jornada
        except json.JSONDecodeError:
            print(f"Error de formato en '{ruta_entrada}'. Revisa las comillas y comas.")
            return None

def cargar_resultados(ruta_resultados=ARCHIVO_RESULTADOS):
    """Lee los resultados reales que se dieron el fin de semana."""
    if not os.path.exists(ruta_resultados):
        print(f"Error: No se encuentra el archivo '{ruta_resultados}'.")
        return None
    
    with open(ruta_resultados, 'r', encoding='utf-8') as archivo:
        try:
            resultados = json.load(archivo)
            print(f"Se han cargado {len(resultados)} resultados desde '{ruta_resultados}'.")
            return resultados
        except json.JSONDecodeError:
            print(f"Error de formato en '{ruta_resultados}'. Revisa las comillas y comas.")
            return None

# ==========================================
# 2. LÓGICA MATEMÁTICA Y ACTUALIZACIÓN
# ==========================================
def obtener_tasa_acierto(datos_fuente):
    """Calcula la tasa de aciertos actual, protegiendo contra divisiones por cero."""
    if datos_fuente['total_predicciones'] == 0:
        return 0.33
    return datos_fuente['aciertos'] / datos_fuente['total_predicciones']

def limpiar_prediccion(diccionario_valores):
    """Detecta si son cuotas (>1) o probabilidades (<1) y devuelve la probabilidad real sin margen."""
    if any(v > 1 for v in diccionario_valores.values()):
        # Son cuotas (ej: 1.80, 3.50, 4.20)
        probs_implicitas = {k: (1 / v) for k, v in diccionario_valores.items()}
        suma_implicitas = sum(probs_implicitas.values())
        return {k: (v / suma_implicitas) for k, v in probs_implicitas.items()}
    else:
        # Son probabilidades puras (ej: 0.50, 0.30, 0.20)
        suma = sum(diccionario_valores.values())
        return {k: (v / suma) for k, v in diccionario_valores.items()}

def calcular_jornada(jornada, db_fuentes):
    """Cruza los datos de la jornada con el historial para obtener tu predicción final."""
    resultados_jornada = []
    
    for partido in jornada:
        suma_tasas = sum(obtener_tasa_acierto(db_fuentes[id_f]) for id_f in partido['predicciones'])
        prob_finales = {'1': 0.0, 'X': 0.0, '2': 0.0}
        
        for id_fuente, probs_brutas in partido['predicciones'].items():
            # Limpiamos los datos de entrada automáticamente
            probs_limpias = limpiar_prediccion(probs_brutas)
            
            tasa = obtener_tasa_acierto(db_fuentes[id_fuente])
            peso = tasa / suma_tasas
            
            prob_finales['1'] += peso * probs_limpias['1']
            prob_finales['X'] += peso * probs_limpias['X']
            prob_finales['2'] += peso * probs_limpias['2']
        
        resultados_jornada.append({
            "partido": f"{partido['local']} vs {partido['visitante']}",
            "probabilidades": prob_finales
        })
        
    return resultados_jornada

def actualizar_estadisticas(jornada, resultados_reales, db_fuentes):
    """Suma puntos basados en la calidad de la probabilidad con Time Decay."""

    # --- 1. APLICAR TIME DECAY ---
    # Usamos la variable global GAMMA_DECAY definida arriba
    for id_fuente in db_fuentes:
        db_fuentes[id_fuente]['aciertos'] *= GAMMA_DECAY
        db_fuentes[id_fuente]['total_predicciones'] *= GAMMA_DECAY

    # --- 2. EVALUAR LA NUEVA JORNADA ---
    for partido in jornada:
        id_p = str(partido['id_partido'])
        if id_p not in resultados_reales or resultados_reales[id_p] == "?":
            continue
            
        resultado_real = resultados_reales[id_p]
        
        for id_fuente, probs_brutas in partido['predicciones'].items():
            db_fuentes[id_fuente]['total_predicciones'] += 1
            
            # Limpiamos los datos (cuotas a probabilidades)
            probs_limpias = limpiar_prediccion(probs_brutas)
            
            # Lógica Brier Score
            brier_sum = 0.0
            for opcion in ['1', 'X', '2']:
                prob_real = 1.0 if opcion == resultado_real else 0.0
                prob_predicha = probs_limpias.get(opcion, 0.0)
                brier_sum += (prob_predicha - prob_real) ** 2
            
            puntuacion = 1 - (brier_sum / 2)
            db_fuentes[id_fuente]['aciertos'] += puntuacion
                
    return db_fuentes