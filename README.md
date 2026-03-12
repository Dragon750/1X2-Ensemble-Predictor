# ⚽ Modelo Predictivo 1X2 por Ensamblado Dinámico (Ensemble Model)

*🌍 Read this in [English](README.en.md)*

Este proyecto es un sistema de pronósticos deportivos basado en Python que utiliza el principio de **Ensemble Learning** (Aprendizaje por Conjuntos). Consolida las cuotas y probabilidades de múltiples fuentes (casas de apuestas *sharp* y modelos de *Big Data*) para calcular la probabilidad real de un partido (1X2). 

El sistema evalúa el rendimiento semanal de cada fuente y ajusta dinámicamente su "peso" en el modelo, otorgando mayor relevancia matemática a las fuentes con mejor tasa de aciertos histórica.

## ✨ Características Principales

* **Limpieza de Overround Automática:** El algoritmo detecta si la entrada es una probabilidad (ej. `0.45`) o una cuota de apuestas (ej. `2.10`). Si es una cuota, calcula la probabilidad implícita y elimina automáticamente la comisión (margen) de la casa para trabajar con probabilidades puras sobre 1.
* **Evaluación Probabilística (Brier Score):** El sistema no evalúa las predicciones como un simple "acierto o fallo". Utiliza el *Brier Score* invertido para castigar severamente a las fuentes que fallan predicciones en las que tenían mucha confianza, y premiar a aquellas que son precisas y calibradas.
* **Actualización Dinámica de Pesos:** Las fuentes compiten entre sí. Tras cada jornada, el programa evalúa la puntuación Brier de cada fuente y recalcula su peso para la próxima predicción.
* **Arquitectura Escalable:** El código está completamente separado de los datos (arquitectura basada en JSON), permitiendo añadir infinitas fuentes o partidos sin tocar una sola línea de lógica.
* **Manejo de Datos Faltantes:** Si una fuente no publica datos una semana, el sistema recalcula los pesos proporcionalmente solo con las fuentes disponibles.
* **Decaimiento Temporal (Time Decay)**: Implementa un factor de "olvido" ($\gamma$) **configurable**. Esto permite que los aciertos recientes tengan más peso que los antiguos, haciendo que el modelo se adapte rápidamente a los cambios de rendimiento o rachas de las fuentes.

## 🧮 El Modelo Matemático

El programa utiliza una media ponderada normalizada donde los pesos se recalculan tras cada jornada evaluando la precisión histórica mediante el **Brier Score** y un factor de **Decaimiento Temporal**.

1. **Puntuación por partido:** Para cada partido, se calcula la calidad de la predicción (de 0 a 1) usando el Brier Score invertido:
   $$Puntos = 1 - \frac{\sum_{i \in \{1, X, 2\}} (P_i - O_i)^2}{2}$$

2. **Actualización del Historial (Time Decay):** Antes de sumar los nuevos aciertos, el historial acumulado ($T_i$) se multiplica por el factor de decaimiento ($\gamma$) definido en `GAMMA_DECAY`:
   $$T_i(t) = T_i(t-1) \cdot \gamma + \sum Puntos_{jornada\_actual}$$

3. **Cálculo de Pesos:** El peso ($W_i$) de cada fuente se determina por su proporción de puntos sobre el total del ecosistema:
   $$W_i = \frac{T_i}{\sum_{j=1}^{N} T_j}$$

4. **Probabilidad Consolidada:** La predicción final es la suma ponderada de todas las fuentes:
   $$P_{final}(R) = \sum_{i=1}^{N} W_i \cdot P_i(R)$$

## 📂 Estructura del Proyecto

```text
1X2-predictor/
│
├── data/                   # 📁 Datos JSON (Ignorados en control de versiones)
│   ├── fuentes.json        # Base de datos histórica de aciertos/fallos
│   ├── jornada.json        # Cuotas y probabilidades de la jornada actual
│   └── resultados.json     # Resultados reales para retroalimentar el modelo
│
├── motor.py                    # ⚙️ Core: Lógica matemática y parseo de JSON
├── calcular_probs.py           # ▶️ Script de ejecución pre-partido
├── actualizar_fuentes.py       # ▶️ Script de ejecución post-partido
├── README.md                   # 📄 Documentación del proyecto (Español)
└── README.en.md                # 📄 Documentación del proyecto (Inglés)
```

### ⚙️ Configuración del Modelo

En la cabecera de motor.py puedes ajustar la variable GAMMA_DECAY:

* `1.0`: El modelo recuerda todo el historial por igual (sin decaimiento).

* `0.95`: Recomendado. Equilibrio entre historial y forma actual.

* `0.80`: El modelo olvida rápido el pasado y prioriza mucho las últimas 2-3 semanas.

## 📄 Ejemplos de Archivos de Datos

Para que el algoritmo funcione correctamente, los archivos alojados en la carpeta `data/` deben respetar la siguiente estructura JSON:

### 1. Historial de Fuentes (`data/fuentes.json`)
Este archivo se actualiza automáticamente, pero debes crearlo la primera vez con un historial base para inicializar el sistema.

```json
{
    "F1": {"nombre": "Pinnacle","aciertos": 3.33,"total_predicciones": 10},
    "F2": {"nombre": "Opta Analyst","aciertos": 3.33,"total_predicciones": 10}
}
```

### 2. Entrada de la Jornada (`data/jornada.json`)
Soporta tanto cuotas tradicionales (mayores a 1) como probabilidades directas (menores a 1). El sistema las estandariza de forma automática.

```json
[
    {
        "id_partido": 1,
        "local": "Real Madrid",
        "visitante": "Barcelona",
        "predicciones": {
            "F1": {"1": 2.10, "X": 3.60, "2": 3.40}, 
            "F2": {"1": 0.45, "X": 0.25, "2": 0.30}  
        }
    },
    {
        "id_partido": 2,
        "local": "Getafe",
        "visitante": "Betis",
        "predicciones": {
            "F1": {"1": 0.40, "X": 0.30, "2": 0.30},
            "F2": {"1": 0.40, "X": 0.30, "2": 0.30}
        }
    }
]
```

### 3. Resultados Reales (`data/resultados.json`)
El ID del partido (clave) debe coincidir con los IDs definidos en la jornada. Si un partido se suspende o no se ha jugado, déjalo con una incógnita ? o elimínalo de la lista.

```json
{
    "1": "1",
    "2": "X",
    "3": "2",
    "4": "?"
}
```

## 🚀 Flujo de Trabajo (Cómo usarlo)

El sistema está diseñado para un flujo de trabajo minimalista de dos pasos semanales:

1. Preparación y Cálculo:
    1. Rellena el archivo `data/jornada.json` con los partidos de la jornada y las cuotas/probabilidades de tus fuentes (ej. Pinnacle, Opta, Forebet).
    2. Ejecuta el calculador:
        ```Bash
        python calcular_probs.py
        ```
    3. El programa imprimirá en consola los porcentajes consolidados y precisos para cada posible resultado (1, X, 2).

2. Retroalimentación del Modelo:
    1. Tras finalizar la jornada, abre `data/resultados.json` y sustituye las incógnitas por los resultados reales ("1", "X" o "2").
    2. Ejecuta el actualizador:
        ```Bash
        python actualizar_fuentes.py
        ```
    3. El sistema evaluará las predicciones hechas el viernes, sumará los aciertos/fallos, actualizará el archivo `fuentes.json` y mostrará el nuevo ranking de fiabilidad de tus fuentes.

## 📌 Fuentes Recomendadas Integradas
El modelo está configurado inicialmente para balancear el "dinero inteligente" del mercado con simulaciones de datos puros:
* **Sharp Bookmakers:** Pinnacle, Betfair Exchange.
* **Agregadores de Mercado:** OddsPortal.
* **Modelos Predictivos (Data Science):** Opta Analyst, Forebet, FootyStats.
* **Sabiduría de Masas:** BeSoccer.
