import sqlite3
import json
import os
import motor
import set_up_db

ARCHIVO_BACKUP = os.path.join(motor.CARPETA_DATOS, "backup_total.json")

def restaurar_copia_completa():
    """Restaura fuentes, partidos y predicciones desde el backup JSON."""
    print("--- 🔄 INICIANDO RESTAURACIÓN COMPLETA 🔄 ---")

    if not os.path.exists(ARCHIVO_BACKUP):
        print(f"❌ Error: No se encontró el archivo '{ARCHIVO_BACKUP}'.")
        return

    try:
        with open(ARCHIVO_BACKUP, "r", encoding="utf-8") as archivo:
            datos_backup = json.load(archivo)
    except Exception as error:
        print(f"❌ Error al leer el JSON de backup: {error}")
        return

    print("🛠️ Verificando estructura de la base de datos...")
    set_up_db.inicializar_tablas_historial()

    conexion = sqlite3.connect(motor.ARCHIVO_SQLITE)
    cursor = conexion.cursor()

    try:
        # 1) Restaurar fuentes agregadas por liga.
        if "fuentes" in datos_backup:
            for fuente in datos_backup["fuentes"]:
                cursor.execute('''
                    INSERT OR REPLACE INTO fuentes (id_fuente, liga, nombre, aciertos, total_predicciones)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    fuente["id_fuente"],
                    fuente["liga"],
                    fuente["nombre"],
                    fuente["aciertos"],
                    fuente["total_predicciones"],
                ))

        # 2) Restaurar historial de partidos ya jugados.
        if "partidos" in datos_backup:
            for partido in datos_backup["partidos"]:
                cursor.execute('''
                    INSERT OR REPLACE INTO partidos (id_partido, liga, local, visitante, resultado_real)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    partido["id_partido"],
                    partido["liga"],
                    partido["local"],
                    partido["visitante"],
                    partido["resultado_real"],
                ))

        # 3) Restaurar probabilidades que emitió cada fuente.
        if "predicciones" in datos_backup:
            for prediccion in datos_backup["predicciones"]:
                cursor.execute('''
                    INSERT OR REPLACE INTO predicciones (id_partido, id_fuente, prob_1, prob_X, prob_2)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    prediccion["id_partido"],
                    prediccion["id_fuente"],
                    prediccion["prob_1"],
                    prediccion["prob_X"],
                    prediccion["prob_2"],
                ))

        conexion.commit()
        print("✅ ¡Restauración completada con éxito!")
        print(f"📊 Se restauraron {len(datos_backup.get('fuentes', []))} fuentes, {len(datos_backup.get('partidos', []))} partidos y {len(datos_backup.get('predicciones', []))} predicciones exactas.")

    except Exception as error:
        print(f"❌ Error crítico al escribir en la base de datos: {error}")
        conexion.rollback()
    finally:
        conexion.close()

if __name__ == "__main__":
    restaurar_copia_completa()