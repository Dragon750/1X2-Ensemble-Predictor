# ⚽ Dynamic Ensemble 1X2 Predictive Model

*Leer en [Español](README.md)*

This project is a sports forecasting system built in Python that leverages the principle of **Ensemble Learning**. It aggregates odds and probabilities from multiple sources (*sharp* bookmakers and *Big Data* models) to calculate the true probability of a football match outcome (1X2).

The system evaluates the weekly performance of each source and dynamically adjusts its "weight" in the model, granting greater mathematical relevance to sources with a better historical hit rate.

## ✨ Key Features

* **Automatic Overround Removal:** The algorithm detects whether the input is a pure probability (e.g., `0.45`) or betting odds (e.g., `2.10`). If it's an odd, it calculates the implied probability and automatically removes the bookmaker's margin (overround) to work with pure probabilities summing to 1.
* **Probabilistic Evaluation (Brier Score):** The system doesn't evaluate predictions as a simple "hit or miss". It uses the inverted *Brier Score* to heavily penalize sources that fail predictions they were highly confident about, and rewards those that are precise and well-calibrated.
* **Dynamic Weight Updating:** Sources compete against each other. After each matchday, the program evaluates the Brier score of each source and recalculates its weight for the next prediction.
* **Scalable Architecture:** The code is completely separated from the data (JSON-based architecture), allowing you to add infinite sources or matches without touching a single line of logic.
* **Missing Data Handling:** If a source fails to publish data for a specific week, the system recalculates weights proportionally using only the available sources.

## 🧮 The Mathematical Model

The program uses a normalized weighted average, but the weights are calculated by evaluating the historical quality of predicted probabilities using the **Brier Score**.

For each match, the squared difference between the predicted probability $P_i$ and the actual outcome $O_i$ is calculated (where $O_i = 1$ if the event occurs and $0$ if it doesn't):

$$Brier = \sum_{i \in \{1, X, 2\}} (P_i - O_i)^2$$

The system inverts this score to convert it into "Quality Points" (from 0 to 1, with 1 being absolute perfection):

$$Puntos = 1 - \frac{Brier}{2}$$

These historically accumulated points ($T_i$) dictate the weight ($W_i$) of each source for future matchdays:

$$W_i = \frac{T_i}{\sum_{j=1}^{N} T_j}$$

Finally, the system's consolidated probability is calculated by summing the product of each source's individual probabilities $P_i(R)$ by its assigned weight:

$$P_{final}(R) = \sum_{i=1}^{N} W_i \cdot P_i(R)$$

## 📂 Project Structure

```text
1X2-predictor/
│
├── data/                   # 📁 JSON Data (Ignored in version control)
│   ├── fuentes.json        # Historical database of hits/misses (points)
│   ├── jornada.json        # Current matchday odds and probabilities
│   └── resultados.json     # Real outcomes to feed back the model
│
├── motor.py                    # ⚙️ Core: Math logic and JSON parsing
├── calcular_probs.py           # ▶️ Pre-match execution script
├── actualizar_fuentes.py       # ▶️ Post-match execution script
└── README.md                   # 📄 Project documentation (Spanish)
└── README.en.md                # 📄 Project documentation (English)
```

## 📄 Data Files Examples

For the algorithm to work correctly, the files hosted in the `data/` folder must respect the following JSON structure:

### 1. Sources History (`data/fuentes.json`)
This file updates automatically, but you must create it the first time with a base history to initialize the system.

```json
{
    "F1": {"nombre": "Pinnacle","aciertos": 3.33,"total_predicciones": 10},
    "F2": {"nombre": "Opta Analyst","aciertos": 3.33,"total_predicciones": 10}
}
```

### 2. Matchday Input (`data/jornada.json`)
It supports both traditional odds (greater than 1) and direct probabilities (less than 1). The system standardizes them automatically.

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

### 3. Real Outcomes (`data/resultados.json`)
The match ID (key) must match the IDs defined in the matchday input. If a match is suspended or hasn't been played yet, leave it with a question mark ? or remove it from the list.

```json
{
    "1": "1",
    "2": "X",
    "3": "2",
    "4": "?"
}
```

## 🚀 Workflow (How to use it)

The system is designed for a minimalist two-step weekly workflow:

1. Preparation and Calculation:

    1. Fill the `data/jornada.json` file with the matchday games and the odds/probabilities from your sources (e.g., Pinnacle, Opta, Forebet).

    2. Run the calculator:
        ```Bash
        python calcular_probs.py
        ```
    3. The program will print the consolidated and precise percentages for each possible outcome (1, X, 2) in the console.

2. Model Feedback:

    1. After the matchday ends, open `data/resultados.json` and replace the question marks with the real outcomes ("1", "X", or "2").

    2. Run the updater:
        ```Bash
        python calcular_probs.py
        ```
    3. The system will evaluate the predictions made on Friday, sum the hits/misses, update the `fuentes.json` file, and show the new reliability ranking of your sources.

## 📌 Fuentes Recomendadas Integradas
The model is initially configured to balance the market's "smart money" with pure data simulations:
* **Sharp Bookmakers:** Pinnacle, Betfair Exchange.
* **Market Aggregators:** OddsPortal.
* **Predictive Models (Data Science):** Opta Analyst, Forebet, FootyStats.
* **Wisdom of the Crowds:** BeSoccer.