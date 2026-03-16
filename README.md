# ⚽ Modelo Predictivo 1X2 por Ensamblado Dinámico (Ensemble Model)

*🌍 Read this in [English](README.en.md)*

Este proyecto es un sistema de pronósticos deportivos basado en Python que utiliza el principio de **Ensemble Learning** (Aprendizaje por Conjuntos). Consolida las cuotas y probabilidades de múltiples fuentes (casas de apuestas *sharp* y modelos de *Big Data*) para calcular la probabilidad real de un partido (1X2). 

El sistema evalúa el rendimiento semanal de cada fuente y ajusta dinámicamente su "peso" en el modelo, guardando un registro histórico inmutable en una base de datos SQLite para otorgar mayor relevancia matemática a las fuentes con mejor tasa de aciertos histórica.

## ✨ Características Principales

* **Limpieza de Overround Automática:** El algoritmo detecta si la entrada es una probabilidad (ej. `0.45`) o una cuota de apuestas (ej. `2.10`). Si es una cuota, calcula la probabilidad implícita y elimina automáticamente la comisión (margen) de la casa para trabajar con probabilidades puras sobre 1.

* **Evaluación Probabilística (Brier Score):** El sistema no evalúa las predicciones como un simple "acierto o fallo". Utiliza el *Brier Score* invertido para castigar severamente a las fuentes que fallan predicciones en las que tenían mucha confianza, y premiar a aquellas que son precisas y calibradas.

* **Segmentación por Ligas:** La base de datos guarda el rendimiento de manera independiente para cada liga. Una fuente puede tener un peso altísimo en la Premier League y uno muy bajo en LaLiga, optimizando las predicciones.

* **Asignación Justa en Memoria (1/3):** Si una fuente es nueva en una liga, el motor le asigna temporalmente una probabilidad natural de acierto del 33.33% (1/3) para realizar el cálculo de pesos, sin contaminar la base de datos con perfiles vacíos.

* **Validación Estricta de Ligas:** El sistema bloquea cálculos y actualizaciones erróneas si detecta que falta la asignación de liga en algún partido del archivo de entrada.

* **Privacidad de Fuentes:** Utiliza un archivo JSON local (ignorado en repositorios) para traducir los IDs de las fuentes a sus nombres reales, protegiendo tu estrategia.

* **Base de Datos Relacional y Backup Completo:** Guarda un historial en SQLite y cuenta con scripts dedicados para exportar e importar la totalidad de la base de datos (fuentes, partidos y predicciones).

* **Manejo de Datos Faltantes:** Si una fuente no publica datos una semana, el sistema recalcula los pesos proporcionalmente solo con las fuentes disponibles.

* **Decaimiento Temporal (Time Decay)**: Implementa un factor de "olvido" ($\gamma$) **configurable**. Esto permite que los aciertos recientes tengan más peso que los antiguos, haciendo que el modelo se adapte rápidamente a los cambios de rendimiento o rachas de las fuentes.

* **Validación Estricta de Datos (Pydantic):** El sistema verifica que los archivos JSON de entrada cumplan un contrato estricto de tipos y formatos. Si detecta un error humano (ej. un campo vacío o un texto en lugar de un número), el programa no falla, sino que lo intercepta y muestra un mensaje amigable indicando exactamente en qué partido y campo está el error.

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
├── data/                       # 📁 Datos (Ignorados en control de versiones)
│   ├── database.db             # Base de datos SQLite (Historial de partidos y fuentes)
│   ├── backup_total.json       # Copia de seguridad completa
│   ├── nombres_fuentes.json    # Diccionario privado de fuentes
│   ├── jornada.json            # Cuotas y probabilidades de la jornada actual
│   └── resultados.json         # Resultados reales para retroalimentar el modelo
│
├── motor.py                    # ⚙️ Core: Lógica matemática y parseo 
├── set_up_db.py                # 🛠️ Script para crear la base de datos
├── backup_completo.py          # 💾 Script para exportar la base de datos a JSON
├── restaurar_completo.py       # 🔄 Script para reconstruir la base de datos desde el JSON
├── calcular_probs.py           # ▶️ Script de ejecución pre-partido
├── actualizar_fuentes.py       # ▶️ Script de ejecución post-partido
├── README.md                   # 📄 Documentación del proyecto (Español)
└── README.en.md                # 📄 Documentación del proyecto (Inglés)
```

## ⚙️ Configuración del Modelo

En la cabecera de `motor.py` puedes ajustar el decaimiento temporal (GAMMA_DECAY).

**Nombres de fuentes privados**: Para mantener tus fuentes en secreto, crea un archivo local llamado `data/nombres_fuentes.json`. Traducirá los IDs cortos a nombres legibles en la consola y la base de datos:

```json
{
    "F1": "Pinnacle",
    "F2": "Opta Analyst"
}
```

## 📄 Ejemplos de Archivos de Datos

Para que el algoritmo funcione correctamente, los archivos alojados en la carpeta `data/` deben respetar la siguiente estructura JSON:

### 1. Entrada de la Jornada (`data/jornada.json`)

Soporta tanto cuotas tradicionales (mayores a 1) como probabilidades directas (menores a 1). El sistema las estandariza de forma automática. **Es vital incluir la etiqueta `liga`**.

```json
[
    {
        "id_partido": 1,
        "liga": "LaLiga",
        "local": "Real Madrid",
        "visitante": "Barcelona",
        "predicciones": {
            "F1": {"1": 2.10, "X": 3.60, "2": 3.40}, 
            "F2": {"1": 0.45, "X": 0.25, "2": 0.30}  
        }
    },
    {
        "id_partido": 2,
        "liga": "LaLiga",
        "local": "Getafe",
        "visitante": "Betis",
        "predicciones": {
            "F1": {"1": 0.40, "X": 0.30, "2": 0.30},
            "F2": {"1": 0.40, "X": 0.30, "2": 0.30}
        }
    }
]
```

### 2. Resultados Reales (`data/resultados.json`)

El ID del partido (clave) debe coincidir con los IDs definidos en la jornada. Las claves deben ser de texto (entre comillas). Si un partido se suspende o no se ha jugado, déjalo con una incógnita `?` o elimínalo de la lista.

```json
{
    "1": "1",
    "2": "X",
    "3": "2",
    "4": "?"
}
```

## 📦 Instalación

El proyecto utiliza dependencias externas para la validación estricta de datos (Pydantic). Antes de ejecutarlo por primera vez, instala las librerías necesarias utilizando el archivo de requisitos:

```bash
pip install -r requirements.txt
```

## 🚀 Flujo de Trabajo (Cómo usarlo)

El sistema está diseñado para un flujo de trabajo minimalista de dos pasos semanales:

0. Mantenimiento e inicialización:

    * **Primera vez**: Ejecuta `python set_up_db.py` para crear el archivo `database.db`.

    * **Copias de seguridad**: Ejecuta `python backup_completo.py` cuando desees respaldar tu progreso en `fuentes_backup.json`. Si hay algún fallo, usa `python restaurar_completo.py` para restaurar tu base de datos.

1. Preparación y Cálculo (Antes de la jornada):

    * Rellena el archivo `data/jornada.json` con los partidos de la jornada y las cuotas/probabilidades de tus fuentes.

    * Ejecuta el calculador `python calcular_probs.py` para obtener los porcentajes ponderados por liga

2. Retroalimentación del Modelo:

    * Tras finalizar la jornada, abre `data/resultados.json` y sustituye las incógnitas por los resultados reales `("1", "X" o "2")`.

    * Ejecuta el actualizador `python actualizar_fuentes.py`, y el sistema mostrará el nuevo ranking de fiabilidad por liga.

## 📌 Fuentes Recomendadas Integradas

El modelo está configurado inicialmente para balancear el "dinero inteligente" del mercado con simulaciones de datos puros:

* **Sharp Bookmakers:** Pinnacle, Betfair Exchange.

* **Agregadores de Mercado:** OddsPortal.

* **Modelos Predictivos (Data Science):** Opta Analyst.

* **Sabiduría de Masas:** BeSoccer.
