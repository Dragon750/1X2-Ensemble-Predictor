import motor

print("--- 🔄 ACTUALIZANDO ESTADÍSTICAS 🔄 ---")

# 1. Cargar todos los archivos necesarios (el motor ya sabe las rutas)
jornada_pasada = motor.cargar_jornada()
if jornada_pasada is None:
    exit()

resultados_fin_de_semana = motor.cargar_resultados()
if resultados_fin_de_semana is None:
    exit()

mis_fuentes = motor.cargar_db()
if mis_fuentes is None:
    exit()

# 2. Realizar la evaluación
mis_fuentes_actualizadas = motor.actualizar_estadisticas(jornada_pasada, resultados_fin_de_semana, mis_fuentes)

# 3. Guardar el nuevo historial
motor.guardar_db(mis_fuentes_actualizadas)

# 4. Mostrar cómo queda el ranking de tus fuentes
print("\n--- NUEVO ESTADO DE TUS FUENTES ---")
for id_f, datos in mis_fuentes_actualizadas.items():
    tasa = motor.obtener_tasa_acierto(datos)
    print(f"{datos['nombre']}:")
    print(f"{datos['aciertos']} aciertos de {datos['total_predicciones']} totales ({tasa:.2%}%)")