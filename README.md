# GetAround Analysis — Bloc 5 Deployment

**Jedha Bootcamp · CDSD Certification · Deployment**

GetAround est la plateforme de location de voitures entre particuliers (fondée en 2009). Ce projet répond à deux enjeux data : **analyse des retards de checkout** (délai minimum entre deux locations) et **optimisation des prix journaliers** via Machine Learning.

---

## Contexte

Lors d’une location, conducteur et propriétaire passent par un flux **check-in / check-out** (état du véhicule, carburant, kilomètres). Les retours en retard génèrent des frictions pour la location suivante.

GetAround envisage un **délai minimum** entre deux réservations sur le même véhicule. Il faut trouver le bon compromis entre :

- réduction des conflits / retards pour le conducteur suivant ;
- impact sur les revenus propriétaires et la disponibilité des annonces.

**Questions produit (Delay Analysis) :**

1. Quelle part du revenu propriétaire serait impactée ?
2. Combien de locations selon le seuil et le scope (tous véhicules vs Connect only) ?
3. À quelle fréquence les conducteurs sont-ils en retard ? Impact sur le suivant ?
4. Combien de cas problématiques résolus selon seuil / scope ?

**Pricing :** suggérer un **prix journalier optimal** pour les propriétaires (endpoint ML `/predict`).

---

## Livrables

| Livrable | Emplacement |
|----------|-------------|
| Dashboard en production | Streamlit — voir [Dashboard](#dashboard-streamlit) |
| Code source | Ce dépôt GitHub |
| API documentée en ligne | FastAPI `/docs` — URL de prod à renseigner |
| Endpoint `POST /predict` | `api/main.py` |
| Notebooks d’analyse & ML | `notebooks/` |
| Tracking MLflow | [https://raphael-nk-getaround-mlflow.hf.space](https://raphael-nk-getaround-mlflow.hf.space) — expérience `getaround-pricing` |

---

## Structure du projet

```
projet-getaround-bloc5/
├── api/
│   ├── main.py                 # FastAPI — /health, /predict, /docs
│   └── models/                 # Modèle exporté (fallback local)
├── dashboard/
│   ├── main.py                 # Dashboard Streamlit (delay + pricing + API)
│   ├── users.json.dist         # Template utilisateurs (copier → users.json)
│   └── assets/
├── data/
│   ├── get_around_delay_analysis.xlsx
│   └── get_around_pricing_project.csv
├── notebooks/
│   ├── 01_delay_analysis_eda.ipynb
│   ├── 02_pricing_eda_feature_eng.ipynb
│   └── 03_model_training_eval.ipynb
├── outputs/
│   ├── images/                 # Figures exportées (présentation)
│   └── models/
├── .env.dist                   # Variables d'environnement (template)
├── pyproject.toml
└── README.md
```

---

## Prérequis

- **Python** ≥ 3.12
- **[uv](https://docs.astral.sh/uv/)** (gestionnaire de dépendances)
- Données dans `data/` (fichiers fournis par Jedha)
- Pour MLflow distant : PostgreSQL + stockage S3 (MinIO/AWS) configurés dans `.env`

---

## Installation locale

```bash
git clone <url-du-repo>
cd projet-getaround-bloc5

uv sync
cp .env.dist .env
# Éditer .env avec vos identifiants MLflow / AWS

cp dashboard/users.json.dist dashboard/users.json
# Éditer dashboard/users.json si besoin
```

---

## Configuration (`.env`)

Copier `.env.dist` vers `.env` et renseigner :

| Variable | Description |
|----------|-------------|
| `MLFLOW_BACKEND_STORE_URI` | URI Postgres pour le backend MLflow **server** |
| `MLFLOW_SERVER_URI` | URL HTTP du tracking client / API (prod : `https://raphael-nk-getaround-mlflow.hf.space`, local : `http://127.0.0.1:5000`) |
| `MLFLOW_EXPERIMENT` | Nom de l’expérience (défaut : `getaround-pricing`) |
| `MLFLOW_PRODUCTION_RUN_ID` | *(optionnel)* Forcer un run production précis |
| `ARTIFACT_ROOT` | Racine artefacts S3 (`s3://...`) |
| `AWS_*` / `MLFLOW_S3_ENDPOINT_URL` | Credentials stockage artefacts |

---

## Notebooks

| Notebook | Rôle |
|----------|------|
| `01_delay_analysis_eda.ipynb` | EDA retards, KPIs, recommandations PM |
| `02_pricing_eda_feature_eng.ipynb` | EDA pricing, feature engineering |
| `03_model_training_eval.ipynb` | Entraînement, tuning (GridSearch / Optuna), export modèle, MLflow, images |

Exécuter dans l’ordre. Le notebook 3 exporte :

- `outputs/models/best_pricing_model_xgb.joblib`
- `api/models/best_pricing_model_xgb.pkl`
- `outputs/images/*.png` (figures présentation)
- Run MLflow `production-best-model` (si serveur actif)

---

## MLflow (tracking)

**Production (Hugging Face Space) :** [https://raphael-nk-getaround-mlflow.hf.space](https://raphael-nk-getaround-mlflow.hf.space)

Déployé via le Space [`raphael-nk/getaround-mlflow`](https://huggingface.co/spaces/raphael-nk/getaround-mlflow) (`mlflow/Dockerfile`). Pour les clients (notebook 03, API), définir `MLFLOW_SERVER_URI=https://raphael-nk-getaround-mlflow.hf.space` dans `.env`.

**Terminal 1 — serveur local (optionnel) :**

```bash
source .venv/bin/activate
set -a && source .env && set +a

mlflow server \
  --backend-store-uri "$MLFLOW_BACKEND_STORE_URI" \
  --default-artifact-root "$ARTIFACT_ROOT" \
  --host 0.0.0.0 \
  --port 5000
```

UI : [http://127.0.0.1:5000](http://127.0.0.1:5000)

Lancer le notebook 3 **après** le serveur pour logger les runs. Sans serveur, l’entraînement et l’export local fonctionnent toujours.

### MLflow en Docker (sans Compose)

Un seul **`mlflow/Dockerfile`** (pas de `docker-compose`, compatible avec les environnements qui n’acceptent qu’une image Docker, ex. **Hugging Face Docker Space**).

```bash
# depuis la racine du dépôt
docker build -f mlflow/Dockerfile -t getaround-mlflow:latest .

# variables depuis .env local (recommandé si vous ne voulez pas baker les secrets dans l’image)
docker run --rm -p 5000:5000 --env-file .env getaround-mlflow:latest
```

**Hugging Face :** renseigner `MLFLOW_BACKEND_STORE_URI`, `ARTIFACT_ROOT` et les clés AWS / S3 dans les **variables / secrets** du Space. L’image écoute **`$PORT`** (défaut **5000** en local). Le conteneur fait `source /app/.env` au démarrage : si ce fichier contient les mêmes clés que le Space, les valeurs du fichier **priment** ; pour n’utiliser que les variables HF, évitez de baker un `.env` avec ces clés ou laissez un `/app/.env` minimal (ex. uniquement `.env.dist` sans secrets réels).

---

## API FastAPI

**Terminal 2 :**

```bash
set -a && source .env && set +a
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/` | GET | Infos service |
| `/health` | GET | Statut + source du modèle (`mlflow` ou `local`) |
| `/predict` | POST | Prédiction prix journalier (EUR) |
| `/docs` | GET | Documentation Swagger (OpenAPI) |

**Chargement du modèle :** priorité au run MLflow `production` (tag `stage=production`), sinon `api/models/best_pricing_model_xgb.pkl`.

### Exemple `POST /predict`

**Requête :**

```json
{
  "input": [
    {
      "model_key": "Citroën",
      "mileage": 50000,
      "engine_power": 90,
      "fuel": "diesel",
      "paint_color": "black",
      "car_type": "hatchback",
      "private_parking_available": true,
      "has_gps": true,
      "has_air_conditioning": true,
      "automatic_car": false,
      "has_getaround_connect": true,
      "has_speed_regulator": true,
      "winter_tires": false
    }
  ]
}
```

**Réponse :**

```json
{
  "prediction": [112.45]
}
```

### cURL

```bash
curl -i -H "Content-Type: application/json" -X POST \
  -d '{"input":[{"model_key":"Citroën","mileage":50000,"engine_power":90,"fuel":"diesel","paint_color":"black","car_type":"hatchback","private_parking_available":true,"has_gps":true,"has_air_conditioning":true,"automatic_car":false,"has_getaround_connect":true,"has_speed_regulator":true,"winter_tires":false}]}' \
  http://127.0.0.1:8000/predict
```

### Python

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/predict",
    json={
        "input": [
            {
                "model_key": "Citroën",
                "mileage": 50000,
                "engine_power": 90,
                "fuel": "diesel",
                "paint_color": "black",
                "car_type": "hatchback",
                "private_parking_available": True,
                "has_gps": True,
                "has_air_conditioning": True,
                "automatic_car": False,
                "has_getaround_connect": True,
                "has_speed_regulator": True,
                "winter_tires": False,
            }
        ]
    },
)
print(response.json())
```

---

## Dashboard Streamlit

```bash
uv run streamlit run dashboard/main.py
```

Ouvrir l’URL affichée (souvent [http://localhost:8501](http://localhost:8501)).

**Fonctionnalités :**

- Analyse des retards (KPIs, seuils, scope Connect)
- Pricing & simulateur de prédiction (appel API locale)
- Suivi modèle / santé API

**Connexion démo :** voir `dashboard/users.json` (template : `users.json.dist`).

Configurer l’URL API dans le dashboard si l’API tourne sur un autre host/port.

---

## Déploiement en production

| Service | URL |
|---------|-----|
| **MLflow** | [https://raphael-nk-getaround-mlflow.hf.space](https://raphael-nk-getaround-mlflow.hf.space) |
| **Dashboard** | `https://<votre-dashboard>/` *(à compléter)* |
| **API** | `https://<votre-api>/` *(à compléter)* |
| **Documentation API** | `https://<votre-api>/docs` *(à compléter)* |
| **Predict** | `https://<votre-api>/predict` *(à compléter)* |

**Exemple production :**

```bash
curl -i -H "Content-Type: application/json" -X POST \
  -d '{"input":[...]}' \
  https://<votre-api>/predict
```

---

## Données

Télécharger / placer dans `data/` :

1. **Delay Analysis** → `get_around_delay_analysis.xlsx`
2. **Pricing Optimization** → `get_around_pricing_project.csv`

---

## Stack technique

- **Python 3.12** · **uv**
- **Pandas** · **scikit-learn** · **XGBoost** · **Optuna**
- **FastAPI** · **Uvicorn**
- **Streamlit**
- **MLflow 1.27** (tracking + artefacts S3)
- **PostgreSQL** · **boto3**

---

## Auteur

**RANJAKASOA Raphaël Marcellin**

Projet réalisé dans le cadre du **Bloc 5 — Deployment**, certification **CDSD**, **Jedha Bootcamp**.

---

*GetAround × Jedha — 2026*
