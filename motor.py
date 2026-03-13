import json
import os
import sqlite3
import datetime

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
    if not os.path.exists(ruta_entrada):
        print(f"Error: No se encuentra el archivo '{ruta_entrada}'.")
        return None
    with open(ruta_entrada, 'r', encoding='utf-8') as archivo:
        try:
            return json.load(archivo)
        except json.JSONDecodeError:
            print(f"Error de formato en '{ruta_entrada}'.")
            return None

def cargar_resultados(ruta_resultados=ARCHIVO_RESULTADOS):
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
    if datos_fuente['total_predicciones'] == 0:
        return 1.0/3.0
    return datos_fuente['aciertos'] / datos_fuente['total_predicciones']

def limpiar_prediccion(diccionario_valores):
    if any(v > 1 for v in diccionario_valores.values()):
        probs_implicitas = {k: (1 / v) for k, v in diccionario_valores.items()}
        suma_implicitas = sum(probs_implicitas.values())
        return {k: (v / suma_implicitas) for k, v in probs_implicitas.items()}
    else:
        suma = sum(diccionario_valores.values())
        return {k: (v / suma) for k, v in diccionario_valores.items()}

def calcular_jornada(jornada, db_fuentes):
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
        
        # Recopilamos las tasas de acierto (en memoria, sin alterar db_fuentes)
        tasas_partido = {}
        for id_fuente in partido['predicciones']:
            # Si existe en la base de datos, usamos su historial real
            if liga in db_fuentes and id_fuente in db_fuentes[liga]:
                tasas_partido[id_fuente] = obtener_tasa_acierto(db_fuentes[liga][id_fuente])
            else:
                # Si es nueva, le damos la probabilidad de azar (1/3) SOLO EN MEMORIA
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
    for liga in db_fuentes:
        for id_fuente in db_fuentes[liga]:
            db_fuentes[liga][id_fuente]['aciertos'] *= GAMMA_DECAY
            db_fuentes[liga][id_fuente]['total_predicciones'] *= GAMMA_DECAY

    for partido in jornada:
        id_p = str(partido['id_partido'])
        if id_p not in resultados_reales or resultados_reales[id_p] == "?":
            continue
            
        # --- NUEVA VALIDACIÓN ESTRICTA ---
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
            
            brier_sum = 0.0
            for opcion in ['1', 'X', '2']:
                prob_real = 1.0 if opcion == resultado_real else 0.0
                prob_predicha = probs_limpias.get(opcion, 0.0)
                brier_sum += (prob_predicha - prob_real) ** 2
            
            puntuacion = 1 - (brier_sum / 2)
            db_fuentes[liga][id_fuente]['aciertos'] += puntuacion
                
    return db_fuentes

def guardar_historial_jornada(jornada, resultados_reales, ruta_db=ARCHIVO_SQLITE):
    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()
    fecha_actual = datetime.datetime.now().strftime("%Y%m%d")

    for partido in jornada:
        id_temporal = str(partido['id_partido']) 
        if id_temporal not in resultados_reales or resultados_reales[id_temporal] == "?":
            continue
            
        # Validamos también aquí por si acaso
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