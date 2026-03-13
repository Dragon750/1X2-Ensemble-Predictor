import json
import os
import motor

# Definimos dónde se guardará el backup usando la configuración de tu motor
ARCHIVO_BACKUP = os.path.join(motor.CARPETA_DATOS, "fuentes_backup.json")

def hacer_copia_seguridad():
    print("--- 💾 INICIANDO COPIA DE SEGURIDAD 💾 ---")
    
    # 1. Extraemos los datos actuales de SQLite usando tu función existente
    datos_actuales = motor.cargar_db()
    
    if not datos_actuales:
        print("⚠️ No se encontraron datos en la base de datos o hubo un error al leerla.")
        return

    # 2. Volcamos ese diccionario a un archivo JSON formateado
    try:
        with open(ARCHIVO_BACKUP, 'w', encoding='utf-8') as archivo:
            # indent=4 lo hace legible para humanos, ensure_ascii=False respeta los acentos
            json.dump(datos_actuales, archivo, indent=4, ensure_ascii=False)
            
        print(f"✅ Copia de seguridad guardada con éxito en: {ARCHIVO_BACKUP}")
        print(f"📊 Se han respaldado los historiales de {len(datos_actuales)} fuentes.")
    except Exception as e:
        print(f"❌ Error al guardar el archivo JSON: {e}")

if __name__ == "__main__":
    hacer_copia_seguridad()