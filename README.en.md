# ⚽ Dynamic Ensemble 1X2 Predictive Model

*🇪🇸 Leer en [Español](README.md)*

This project is a sports forecasting system built in Python that leverages the principle of **Ensemble Learning**. It aggregates odds and probabilities from multiple sources (*sharp* bookmakers and *Big Data* models) to calculate the true probability of a football match outcome (1X2).

The system evaluates the weekly performance of each source and dynamically adjusts its "weight" in the model, keeping an immutable historical record in a SQLite database to grant greater mathematical relevance to sources with a better historical hit rate.

## ✨ Key Features

* **Automatic Overround Removal:** The algorithm detects whether the input is a pure probability (e.g., `0.45`) or betting odds (e.g., `2.10`). If it's an odd, it calculates the implied probability and automatically removes the bookmaker's margin (overround) to work with pure probabilities summing to 1.

* **Probabilistic Evaluation (Brier Score):** The system doesn't evaluate predictions as a simple "hit or miss". It uses the inverted *Brier Score* to heavily penalize sources that fail predictions they were highly confident about, and rewards those that are precise and well-calibrated.

* **League Segmentation:** The database now stores performance metrics separated by league. A source might be highly weighted in the Premier League but penalized in LaLiga.

* **Fair In-Memory Initialization (1/3):** If a source is new to a specific league, the engine temporarily assigns it a natural 33.33% (1/3) hit probability for weight distribution, keeping the database clean of empty profiles.

* **Relational Database (SQLite):** Keeps a full, immutable history of all matches, exact odds, and real outcomes.

* **Backup System:** Includes a quick script to extract all historical data and save it securely into a JSON file.

* **Missing Data Handling:** If a source fails to publish data for a specific week, the system recalculates weights proportionally using only the available sources.

* **Time Decay**: Implements a **configurable** decay factor ($\gamma$). This allows recent results to carry more weight than older ones, ensuring the model adapts quickly to changes in source performance or current trends.

## 🧮 The Mathematical Model

The system uses a normalized weighted average where weights are recalculated after each matchday by evaluating historical accuracy using the **Brier Score** and a **Time Decay** factor.

1. **Match Scoring:** For each match, prediction quality (from 0 to 1) is calculated using the inverted Brier Score:

 $$Points = 1 - \frac{\sum_{i \in \{1, X, 2\}} (P_i - O_i)^2}{2}$$

2. **Historical Update (Time Decay):** Before adding new points, the accumulated history ($T_i$) is multiplied by the decay factor ($\gamma$) defined in `GAMMA_DECAY`:

$$T_i(t) = T_i(t-1) \cdot \gamma + \sum Points_{current\_matchday}$$

3. **Weight Calculation:** The weight ($W_i$) of each source is determined by its proportion of points relative to the total ecosystem:

$$W_i = \frac{T_i}{\sum_{j=1}^{N} T_j}$$

4. **Consolidated Probability:** The final prediction is the weighted sum of all individual sources:

$$P_{final}(R) = \sum_{i=1}^{N} W_i \cdot P_i(R)$$

## 📂 Project Structure

```text
1X2-predictor/
│
├── data/                       # 📁 Data (Ignored in version control)
│   ├── database.db             # SQLite database (History of matches and sources)
│   ├── fuentes_backup.json     # Backup of historical source data
│   ├── jornada.json            # Current matchday odds and probabilities
│   └── resultados.json         # Real outcomes to feed back the model
│
├── motor.py                    # ⚙️ Core logic and JSON parsing
├── set_up_db.py                # 🛠️ Database initialization script
├── backup_fuentes.py           # 💾 JSON backup generator script
├── calcular_probs.py           # ▶️ Pre-match execution script
├── actualizar_fuentes.py       # ▶️ Post-match execution script
├── README.md                   # 📄 Project documentation (Spanish)
└── README.en.md                # 📄 Project documentation (English)
```

## 📄 Data Files Examples

For the algorithm to work correctly, the files hosted in the `data/` folder must respect the following JSON structure:

### 1. Matchday Input (`data/jornada.json`)

It supports both traditional odds (greater than 1) and direct probabilities (less than 1). The system standardizes them automatically. **The `liga`(league) tag is now required**.

```json
[
    {
        "id_partido": 1,
        "liga": "Premier League",
        "local": "Arsenal",
        "visitante": "Chelsea",
        "predicciones": {
            "F1": {"1": 2.10, "X": 3.60, "2": 3.40}, 
            "F2": {"1": 0.45, "X": 0.25, "2": 0.30}  
        }
    }
]
```

### 2. Real Outcomes (`data/resultados.json`)

The match ID (key) must match the IDs defined in the matchday input. If a match is suspended or hasn't been played yet, leave it with a question mark `?` or remove it from the list.

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

0. Setup and Maintenance:
    * **First Run**: Execute `python set_up_db.py` to generate the `database.db` file.

    * **Backups**: Run `python backup_fuentes.py` anytime you want to save a secure JSON copy of your sources' histories.

1. Preparation and Calculation:

    * Fill the `data/jornada.json` file with the matchday games and the odds/probabilities from your sources.

    * Run the calculator `python calcular_probs.py` to get the league-weighted percentages.

2. Model Feedback:

    * After the matchday ends, open `data/resultados.json` and replace the question marks with the real outcomes `("1", "X", or "2")`.

    2. Run the updater `python calcular_probs.py`, and the system will recalculate metrics and see the updated league rankings.

## 📌 Fuentes Recomendadas Integradas
The model is initially configured to balance the market's "smart money" with pure data simulations:

* **Sharp Bookmakers:** Pinnacle, Betfair Exchange.

* **Market Aggregators:** OddsPortal.

* **Predictive Models (Data Science):** Opta Analyst, Forebet, FootyStats.

* **Wisdom of the Crowds:** BeSoccer.