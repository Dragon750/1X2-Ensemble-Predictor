import json
import os
import sqlite3
import datetime

# ==========================================
# CONFIGURACIÓN DE ARCHIVOS Y MODELO
# ==========================================
CARPETA_DATOS = "data"
ARCHIVO_DB = os.path.join(CARPETA_DATOS,"fuentes.json")
ARCHIVO_SQLITE = os.path.join(CARPETA_DATOS, "database.db")
ARCHIVO_ENTRADA = os.path.join(CARPETA_DATOS,"jornada.json")
ARCHIVO_RESULTADOS = os.path.join(CARPETA_DATOS,"resultados.json")
GAMMA_DECAY = 0.95

# ==========================================
# 1. GESTIÓN DE ARCHIVOS (LECTURA Y ESCRITURA)
# ==========================================
def cargar_db(ruta_db=ARCHIVO_DB):
    """Carga las fuentes desde SQLite y devuelve un diccionario para compatibilidad."""
    if not os.path.exists(ruta_db):
        print("Error: Base de datos SQLite no encontrada.")
        return None

    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()
    
    # Obtenemos todos los registros
    cursor.execute("SELECT id_fuente, nombre, aciertos, total_predicciones FROM fuentes")
    filas = cursor.fetchall()
    conexion.close()

    # Reconstruimos el diccionario exacto que espera el resto del código
    db_fuentes = {}
    for fila in filas:
        id_f, nombre, aciertos, total = fila
        db_fuentes[id_f] = {
            "nombre": nombre,
            "aciertos": aciertos,
            "total_predicciones": total
        }
        
    return db_fuentes

def guardar_db(db_fuentes, ruta_db=ARCHIVO_DB):
    """Guarda el diccionario actualizado devuelta en SQLite."""
    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()

    # Usamos INSERT OR REPLACE para actualizar si existe, o crear si es nuevo
    for id_f, datos in db_fuentes.items():
        cursor.execute('''
            INSERT OR REPLACE INTO fuentes (id_fuente, nombre, aciertos, total_predicciones)
            VALUES (?, ?, ?, ?)
        ''', (id_f, datos['nombre'], datos['aciertos'], datos['total_predicciones']))

    conexion.commit()
    conexion.close()

def inicializar_tablas_historial(ruta_db=ARCHIVO_SQLITE):
    """Crea las tablas relacionales para guardar el historial de partidos y cuotas."""
    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()
    
    # 1. Tabla de Partidos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partidos (
            id_partido TEXT PRIMARY KEY,
            local TEXT,
            visitante TEXT,
            resultado_real TEXT
        )
    ''')
    
    # 2. Tabla de Predicciones (Relaciona Partido -> Fuente -> Probabilidades)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predicciones (
            id_partido TEXT,
            id_fuente TEXT,
            prob_1 REAL,
            prob_X REAL,
            prob_2 REAL,
            PRIMARY KEY (id_partido, id_fuente),
            FOREIGN KEY (id_partido) REFERENCES partidos(id_partido),
            FOREIGN KEY (id_fuente) REFERENCES fuentes(id_fuente)
        )
    ''')
    
    conexion.commit()
    conexion.close()

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

def guardar_historial_jornada(jornada, resultados_reales, ruta_db=ARCHIVO_SQLITE):
    """Guarda los metadatos y predicciones generando un ID único para la base de datos."""
    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()

    # Obtenemos la fecha actual para hacer el ID único (ej: "20260312")
    fecha_actual = datetime.datetime.now().strftime("%Y%m%d")

    for partido in jornada:
        # Este es tu ID del JSON (1, 2, 3...), lo usamos solo para buscar el resultado
        id_temporal = str(partido['id_partido']) 
        
        if id_temporal not in resultados_reales or resultados_reales[id_temporal] == "?":
            continue
            
        resultado = resultados_reales[id_temporal]
        
        # --- NUEVO: Generamos el ID Permanente para SQLite ---
        # Quedará algo como: "RealMadrid_Barcelona_20260312"
        local_limpio = partido['local'].replace(" ", "")
        visitante_limpio = partido['visitante'].replace(" ", "")
        id_db = f"{local_limpio}_{visitante_limpio}_{fecha_actual}"
        
        # 1. Insertar el partido usando el id_db permanente
        cursor.execute('''
            INSERT OR IGNORE INTO partidos (id_partido, local, visitante, resultado_real)
            VALUES (?, ?, ?, ?)
        ''', (id_db, partido['local'], partido['visitante'], resultado))
        
        # 2. Insertar las predicciones usando el id_db permanente
        for id_fuente, probs_brutas in partido['predicciones'].items():
            probs_limpias = limpiar_prediccion(probs_brutas)
            
            cursor.execute('''
                INSERT OR REPLACE INTO predicciones (id_partido, id_fuente, prob_1, prob_X, prob_2)
                VALUES (?, ?, ?, ?, ?)
            ''', (id_db, id_fuente, probs_limpias['1'], probs_limpias['X'], probs_limpias['2']))

    conexion.commit()
    conexion.close()