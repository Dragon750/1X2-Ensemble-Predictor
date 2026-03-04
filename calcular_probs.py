import motor

print("--- ⚽ PREPARANDO LA JORNADA ⚽ ---")

# 1. Cargar los archivos (el motor ya sabe las rutas)
jornada_semana = motor.cargar_jornada()
if jornada_semana is None:
    exit()

mis_fuentes = motor.cargar_db()
if mis_fuentes is None:
    exit()

# 2. Calcular probabilidades matemáticas
predicciones_finales = motor.calcular_jornada(jornada_semana, mis_fuentes)

# 3. Imprimir el resultado para que rellenes la porra
print("\n--- TUS PREDICCIONES PONDERADAS ---")
for res in predicciones_finales:
    prob_1 = res['probabilidades']['1']
    prob_X = res['probabilidades']['X']
    prob_2 = res['probabilidades']['2']
    
    print(f"{res['partido']}:")
    print(f"1: {prob_1:6.2%}  |  X: {prob_X:6.2%}  |  2: {prob_2:6.2%}")