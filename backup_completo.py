import sqlite3
import json
import os
import motor

ARCHIVO_BACKUP = os.path.join(motor.CARPETA_DATOS, "backup_total.json")

def dict_factory(cursor, row):
    """Convierte las filas de SQLite en diccionarios de Python automáticamente."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def hacer_copia_completa():
    print("--- 💾 INICIANDO COPIA DE SEGURIDAD COMPLETA 💾 ---")
    
    if not os.path.exists(motor.ARCHIVO_SQLITE):
        print("⚠️ No se encontró la base de datos SQLite. No hay nada que respaldar.")
        return

    conexion = sqlite3.connect(motor.ARCHIVO_SQLITE)
    conexion.row_factory = dict_factory # Hace que los resultados sean diccionarios
    cursor = conexion.cursor()
    
    datos_completos = {}
    tablas = ['fuentes', 'partidos', 'predicciones']
    
    try:
        for tabla in tablas:
            cursor.execute(f"SELECT * FROM {tabla}")
            datos_completos[tabla] = cursor.fetchall()
            
        with open(ARCHIVO_BACKUP, 'w', encoding='utf-8') as archivo:
            json.dump(datos_completos, archivo, indent=4, ensure_ascii=False)
            
        print(f"✅ Copia de seguridad guardada con éxito en: {ARCHIVO_BACKUP}")
        print(f"📊 Resumen del respaldo:")
        print(f"   - Fuentes: {len(datos_completos['fuentes'])} registros")
        print(f"   - Partidos: {len(datos_completos['partidos'])} registros")
        print(f"   - Predicciones: {len(datos_completos['predicciones'])} registros")
        
    except Exception as e:
        print(f"❌ Error durante el backup: {e}")
    finally:
        conexion.close()

if __name__ == "__main__":
    hacer_copia_completa()