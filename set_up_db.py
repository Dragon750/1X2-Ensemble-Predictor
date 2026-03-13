import sqlite3
import os

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
CARPETA_DATOS = os.path.join(DIRECTORIO_ACTUAL, "data")
ARCHIVO_SQLITE = os.path.join(CARPETA_DATOS, "database.db")

def inicializar_tablas_historial():
    """Crea las tablas relacionales segmentadas por liga."""
    os.makedirs(CARPETA_DATOS, exist_ok=True)
    conexion = sqlite3.connect(ARCHIVO_SQLITE)
    cursor = conexion.cursor()
    
    # 1. Tabla de Fuentes (ahora dividida por LIGA)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fuentes (
            id_fuente TEXT,
            liga TEXT,
            nombre TEXT,
            aciertos REAL,
            total_predicciones REAL,
            PRIMARY KEY (id_fuente, liga)
        )
    ''')

    # 2. Tabla de Partidos (ahora guarda a qué liga pertenece)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partidos (
            id_partido TEXT PRIMARY KEY,
            liga TEXT,
            local TEXT,
            visitante TEXT,
            resultado_real TEXT
        )
    ''')
    
    # 3. Tabla de Predicciones (se mantiene unida al partido)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predicciones (
            id_partido TEXT,
            id_fuente TEXT,
            prob_1 REAL,
            prob_X REAL,
            prob_2 REAL,
            PRIMARY KEY (id_partido, id_fuente),
            FOREIGN KEY (id_partido) REFERENCES partidos(id_partido)
        )
    ''')
    
    conexion.commit()
    conexion.close()
    print("✅ Base de datos segmentada por ligas inicializada correctamente en data/database.db")

if __name__ == "__main__":
    inicializar_tablas_historial()