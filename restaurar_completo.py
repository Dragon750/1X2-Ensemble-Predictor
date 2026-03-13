import sqlite3
import json
import os
import motor
import set_up_db

ARCHIVO_BACKUP = os.path.join(motor.CARPETA_DATOS, "backup_total.json")

def restaurar_copia_completa():
    print("--- 🔄 INICIANDO RESTAURACIÓN COMPLETA 🔄 ---")
    
    if not os.path.exists(ARCHIVO_BACKUP):
        print(f"❌ Error: No se encontró el archivo '{ARCHIVO_BACKUP}'.")
        return

    try:
        with open(ARCHIVO_BACKUP, 'r', encoding='utf-8') as archivo:
            datos_backup = json.load(archivo)
    except Exception as e:
        print(f"❌ Error al leer el JSON de backup: {e}")
        return

    print("🛠️ Verificando estructura de la base de datos...")
    set_up_db.inicializar_tablas_historial()

    conexion = sqlite3.connect(motor.ARCHIVO_SQLITE)
    cursor = conexion.cursor()

    try:
        # 1. Restaurar Fuentes
        if 'fuentes' in datos_backup:
            for f in datos_backup['fuentes']:
                cursor.execute('''
                    INSERT OR REPLACE INTO fuentes (id_fuente, liga, nombre, aciertos, total_predicciones)
                    VALUES (?, ?, ?, ?, ?)
                ''', (f['id_fuente'], f['liga'], f['nombre'], f['aciertos'], f['total_predicciones']))

        # 2. Restaurar Partidos
        if 'partidos' in datos_backup:
            for p in datos_backup['partidos']:
                cursor.execute('''
                    INSERT OR REPLACE INTO partidos (id_partido, liga, local, visitante, resultado_real)
                    VALUES (?, ?, ?, ?, ?)
                ''', (p['id_partido'], p['liga'], p['local'], p['visitante'], p['resultado_real']))

        # 3. Restaurar Predicciones
        if 'predicciones' in datos_backup:
            for pr in datos_backup['predicciones']:
                cursor.execute('''
                    INSERT OR REPLACE INTO predicciones (id_partido, id_fuente, prob_1, prob_X, prob_2)
                    VALUES (?, ?, ?, ?, ?)
                ''', (pr['id_partido'], pr['id_fuente'], pr['prob_1'], pr['prob_X'], pr['prob_2']))

        conexion.commit()
        print("✅ ¡Restauración completada con éxito!")
        print(f"📊 Se restauraron {len(datos_backup.get('fuentes', []))} fuentes, {len(datos_backup.get('partidos', []))} partidos y {len(datos_backup.get('predicciones', []))} predicciones exactas.")
        
    except Exception as e:
        print(f"❌ Error crítico al escribir en la base de datos: {e}")
        conexion.rollback()
    finally:
        conexion.close()

if __name__ == "__main__":
    restaurar_copia_completa()