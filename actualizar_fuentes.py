import motor

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

# Mostrar rankings segmentados ordenados de mayor a menor peso
print("\n--- NUEVO ESTADO DE TUS FUENTES POR LIGA ---")
for liga, fuentes_liga in mis_fuentes_actualizadas.items():
    print(f"\n🏆 LIGA: {liga}")
    print("-" * 35)
    
    # 1. Precalculamos la tasa para cada fuente y la guardamos en una lista
    fuentes_ordenadas = []
    for id_f, datos in fuentes_liga.items():
        tasa = motor.obtener_tasa_acierto(datos)
        fuentes_ordenadas.append((id_f, datos, tasa))
        
    # 2. Ordenamos la lista usando la tasa (el tercer elemento, índice 2) de mayor a menor
    fuentes_ordenadas.sort(key=lambda x: x[2], reverse=True)
    
    # 3. Imprimimos ya ordenado
    for id_f, datos, tasa in fuentes_ordenadas:
        nombre = datos.get('nombre', id_f)
        print(f"  {nombre}: {datos['aciertos']:.2f} pts de {datos['total_predicciones']:.0f} totales ({tasa:.2%})")