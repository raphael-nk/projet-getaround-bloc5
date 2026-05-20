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
| Dashboard en production | [https://raphael-nk-getaround-dashboard.hf.space](https://raphael-nk-getaround-dashboard.hf.space) |
| Code source | Ce dépôt GitHub |
| API documentée en ligne | [https://raphael-nk-getaround-api.hf.space/docs](https://raphael-nk-getaround-api.hf.space/docs) |
| Endpoint `POST /predict` | `api/main.py` |
| Notebooks d’analyse & ML | `notebooks/` |
| Tracking MLflow | [https://raphael-nk-getaround-mlflow.hf.space](https://raphael-nk-getaround-mlflow.hf.space) — expérience `getaround-pricing` |

---

## Structure du projet

```
projet-getaround-bloc5/
├── api/
│   ├── main.py                 # FastAPI — /health, /predict, /docs
│   ├── Dockerfile              # Image API (contexte api/)
│   ├── Dockerfile.monorepo     # Image API + .env racine
│   ├── entrypoint.sh
│   └── models/                 # Modèle exporté (fallback local)
├── dashboard/
│   ├── main.py                 # Dashboard Streamlit (delay + pricing + API)
│   ├── Dockerfile              # Space HF — datasets via S3 au démarrage
│   ├── entrypoint.sh
│   ├── sync_data_from_s3.py
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
| `GETAROUND_API_URL` | API pricing (prod : `https://raphael-nk-getaround-api.hf.space`) |
| `GETAROUND_DATA_S3_URI` | Datasets dashboard (ex. `s3://amzn-jedha-39/datasets/getaround/`) |

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

**Production (Hugging Face Space) :** [https://raphael-nk-getaround-api.hf.space](https://raphael-nk-getaround-api.hf.space) · [Swagger `/docs`](https://raphael-nk-getaround-api.hf.space/docs) · [`/health`](https://raphael-nk-getaround-api.hf.space/health)

Déployé via le Space [`raphael-nk/getaround-api`](https://huggingface.co/spaces/raphael-nk/getaround-api) (`api/Dockerfile`). Le modèle est chargé depuis MLflow (run production) si le serveur est joignable, sinon depuis `api/models/best_pricing_model_xgb.pkl` en local.

**Terminal 2 (local) :**

```bash
set -a && source .env && set +a
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### API en Docker (sans Compose)

**`api/Dockerfile.monorepo`** : build depuis la racine (`.env` copié depuis la racine du dépôt).

```bash
docker build -f api/Dockerfile.monorepo -t getaround-api:latest .
docker run --rm -p 7860:7860 getaround-api:latest
# ou variables au runtime : docker run --rm -p 7860:7860 --env-file .env getaround-api:latest
```

**`api/Dockerfile`** : build depuis `api/` (ex. Space HF) — `docker run --env-file ../.env` si `.env` n’est pas dans l’image.

Équivalent conteneur (sans `--reload`) : `uvicorn api.main:app --host 0.0.0.0 --port 7860` ; le port suit **`$PORT`** (défaut **7860**).

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

**Production :**

```bash
curl -s https://raphael-nk-getaround-api.hf.space/health | jq .

curl -i -H "Content-Type: application/json" -X POST \
  -d '{"input":[{"model_key":"Citroën","mileage":50000,"engine_power":90,"fuel":"diesel","paint_color":"black","car_type":"hatchback","private_parking_available":true,"has_gps":true,"has_air_conditioning":true,"automatic_car":false,"has_getaround_connect":true,"has_speed_regulator":true,"winter_tires":false}]}' \
  https://raphael-nk-getaround-api.hf.space/predict
```

**Local :**

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

**Production (Hugging Face Space) :** [https://raphael-nk-getaround-dashboard.hf.space](https://raphael-nk-getaround-dashboard.hf.space)

Déployé via le Space [`raphael-nk/getaround-dashboard`](https://huggingface.co/spaces/raphael-nk/getaround-dashboard). Datasets chargés depuis **`GETAROUND_DATA_S3_URI`** (`s3://amzn-jedha-39/datasets/getaround/`). API de prédiction : **`GETAROUND_API_URL=https://raphael-nk-getaround-api.hf.space`**.

**Local :**

```bash
uv run streamlit run dashboard/main.py
```

Ouvrir l’URL affichée (souvent [http://localhost:8501](http://localhost:8501)).

### Dashboard en Docker (sans Compose)

Depuis `dashboard/` (Space HF) :

```bash
cd dashboard
docker build -t getaround-dashboard:latest .
docker run --rm -p 7860:7860 \
  -e GETAROUND_API_URL=https://raphael-nk-getaround-api.hf.space \
  -e GETAROUND_DATA_S3_URI=s3://amzn-jedha-39/datasets/getaround/ \
  --env-file ../.env \
  getaround-dashboard:latest
```

Le conteneur écoute **`${PORT:-7860}`** (port imposé par Hugging Face).

**Données :** en local, `dashboard/data/` puis `data/` à la racine. Sur le **Space dashboard HF**, les fichiers ne sont pas dans Git : ils sont téléchargés depuis **`GETAROUND_DATA_S3_URI`** (ex. `s3://amzn-jedha-39/datasets/getaround/`) au démarrage via `sync_data_from_s3.py` (credentials **`AWS_*`** dans les secrets HF).

**Fonctionnalités :**

- Analyse des retards (KPIs, seuils, scope Connect)
- Pricing & simulateur de prédiction (appel API locale ou [API HF](https://raphael-nk-getaround-api.hf.space))
- Suivi modèle / santé API

**Connexion démo :** voir `dashboard/users.json` (template : `users.json.dist`).

Pour appeler l’API en production depuis le dashboard : `GETAROUND_API_URL=https://raphael-nk-getaround-api.hf.space` (variable d’environnement ou réglage dans l’app).

---

## Déploiement en production

| Service | URL |
|---------|-----|
| **MLflow** | [https://raphael-nk-getaround-mlflow.hf.space](https://raphael-nk-getaround-mlflow.hf.space) |
| **API** | [https://raphael-nk-getaround-api.hf.space](https://raphael-nk-getaround-api.hf.space) |
| **Documentation API** | [https://raphael-nk-getaround-api.hf.space/docs](https://raphael-nk-getaround-api.hf.space/docs) |
| **Predict** | [https://raphael-nk-getaround-api.hf.space/predict](https://raphael-nk-getaround-api.hf.space/predict) |
| **Dashboard** | [https://raphael-nk-getaround-dashboard.hf.space](https://raphael-nk-getaround-dashboard.hf.space) |

**Exemple production :**

```bash
curl -i -H "Content-Type: application/json" -X POST \
  -d '{"input":[{"model_key":"Citroën","mileage":50000,"engine_power":90,"fuel":"diesel","paint_color":"black","car_type":"hatchback","private_parking_available":true,"has_gps":true,"has_air_conditioning":true,"automatic_car":false,"has_getaround_connect":true,"has_speed_regulator":true,"winter_tires":false}]}' \
  https://raphael-nk-getaround-api.hf.space/predict
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
