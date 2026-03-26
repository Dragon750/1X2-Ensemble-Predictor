"""Actualiza las estadísticas históricas de cada fuente por liga."""

import motor


"""Carga jornada/resultados, actualiza métricas y muestra ranking."""
print("--- 🔄 ACTUALIZANDO ESTADÍSTICAS 🔄 ---")

jornada_pasada = motor.cargar_jornada()
if jornada_pasada is None: exit()

resultados_fin_de_semana = motor.cargar_resultados()
if resultados_fin_de_semana is None: exit()

mis_fuentes = motor.cargar_db()

# Evaluar
mis_fuentes_actualizadas = motor.actualizar_estadisticas(jornada_pasada, resultados_fin_de_semana, mis_fuentes)

# Guardar
motor.guardar_db(mis_fuentes_actualizadas)
motor.guardar_historial_jornada(jornada_pasada, resultados_fin_de_semana)

print("\n--- NUEVO ESTADO DE TUS FUENTES POR LIGA ---")
for liga, fuentes_liga in mis_fuentes_actualizadas.items():
    print(f"\n🏆 LIGA: {liga}")
    print("-" * 35)

    # Ordenamos por tasa de acierto para mostrar primero las fuentes más fiables.
    fuentes_ordenadas = []
    for id_fuente, datos in fuentes_liga.items():
        tasa = motor.obtener_tasa_acierto(datos)
        fuentes_ordenadas.append((id_fuente, datos, tasa))

    fuentes_ordenadas.sort(key=lambda item: item[2], reverse=True)

    for id_fuente, datos, tasa in fuentes_ordenadas:
        nombre = datos.get("nombre", id_fuente)
        print(f"  {nombre}: {datos['aciertos']:.2f} pts de {datos['total_predicciones']:.0f} totales ({tasa:.2%})")
