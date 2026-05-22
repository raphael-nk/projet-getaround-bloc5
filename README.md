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
| Dashboard en production | [raphael-nk-getaround-dashboard.hf.space](https://raphael-nk-getaround-dashboard.hf.space) — submodule [`dashboard/`](dashboard/) → [Space HF](https://huggingface.co/spaces/raphael-nk/getaround-dashboard) |
| API documentée en ligne | [raphael-nk-getaround-api.hf.space/docs](https://raphael-nk-getaround-api.hf.space/docs) — submodule [`api/`](api/) → [Space HF](https://huggingface.co/spaces/raphael-nk/getaround-api) |
| Endpoint `POST /predict` | [`api/main.py`](api/main.py) (submodule API) |
| Tracking MLflow | [raphael-nk-getaround-mlflow.hf.space](https://raphael-nk-getaround-mlflow.hf.space) — submodule [`mlflow/`](mlflow/) → [Space HF](https://huggingface.co/spaces/raphael-nk/getaround-mlflow) — expérience `getaround-pricing` |
| Code source monorepo | Racine GitHub + **3 submodules** (voir [Structure](#structure-du-projet) et [`.gitmodules`](.gitmodules)) |
| Notebooks d’analyse & ML | `notebooks/` (monorepo uniquement) |

---

## Déploiement — vue d’ensemble

| Service | URL production | Repo Hugging Face Space |
|---------|----------------|-------------------------|
| **Dashboard** | [raphael-nk-getaround-dashboard.hf.space](https://raphael-nk-getaround-dashboard.hf.space) | [raphael-nk/getaround-dashboard](https://huggingface.co/spaces/raphael-nk/getaround-dashboard) |
| **API** | [raphael-nk-getaround-api.hf.space](https://raphael-nk-getaround-api.hf.space) · [/docs](https://raphael-nk-getaround-api.hf.space/docs) | [raphael-nk/getaround-api](https://huggingface.co/spaces/raphael-nk/getaround-api) |
| **MLflow** | [raphael-nk-getaround-mlflow.hf.space](https://raphael-nk-getaround-mlflow.hf.space) | [raphael-nk/getaround-mlflow](https://huggingface.co/spaces/raphael-nk/getaround-mlflow) |

**Données (dashboard en prod)** : `s3://amzn-jedha-39/datasets/getaround/`  
Fichiers attendus : `get_around_delay_analysis.xlsx`, `get_around_pricing_project.csv`

En **production**, chaque service est un **Docker Space** Hugging Face. En **local**, vous pouvez lancer la stack complète avec **`docker-compose.yml`** à la racine (voir [Docker Compose](#docker-compose-stack-locale)) ou builder chaque submodule séparément. Le code des Spaces est versionné via des **submodules Git** (voir ci-dessous).

---

## Structure du projet

Le dépôt principal (monorepo GitHub) contient l’analyse, les notebooks et les données locales. Les **trois services en production** sont des **submodules Git** : chaque dossier pointe vers un **Hugging Face Docker Space** (même historique Git que le Space).

### Monorepo (racine)

```
projet-getaround-bloc5/
├── docker-compose.yml          # stack locale MLflow + API + dashboard
├── .gitmodules                 # déclaration des 3 submodules → Spaces HF
├── .env.dist                   # template variables (copier → .env)
├── docs/
│   ├── ARCHITECTURE.md         # Schéma, submodules, flux MLflow 3
│   └── JOURNAL.md              # Journal de bord / migrations
├── pyproject.toml              # dépendances uv (notebooks, dev local)
├── uv.lock
├── requirements.txt
├── README.md
├── LICENSE
├── assets/                     # visuels doc / présentation
├── data/                       # datasets locaux (notebooks & dev)
│   ├── get_around_delay_analysis.xlsx
│   └── get_around_pricing_project.csv
├── notebooks/
│   ├── 01_delay_analysis_eda.ipynb
│   ├── 02_pricing_eda_feature_eng.ipynb
│   └── 03_model_training_eval.ipynb
├── outputs/
│   ├── images/                 # figures exportées (notebook 03)
│   └── models/                 # joblib, CSV comparaison modèles
├── api/                        # ◆ submodule — voir ci-dessous
├── dashboard/                  # ◆ submodule — voir ci-dessous
└── mlflow/                     # ◆ submodule — voir ci-dessous
```

### Submodule `api/` → [raphael-nk/getaround-api](https://huggingface.co/spaces/raphael-nk/getaround-api)

**Space en ligne :** [https://raphael-nk-getaround-api.hf.space](https://raphael-nk-getaround-api.hf.space) · [Swagger `/docs`](https://raphael-nk-getaround-api.hf.space/docs)

```
api/                            # git submodule
├── Dockerfile                  # image Docker Space
├── entrypoint.sh               # uvicorn, port $PORT (7860 sur HF)
├── main.py                     # FastAPI — /health, /predict, /docs
├── __init__.py
├── requirements.txt
├── README.md                   # frontmatter HF (sdk: docker)
├── models/
│   └── .gitkeep                # fallback local best_pricing_model_xgb.pkl
├── .gitignore
└── .gitattributes
```

### Submodule `mlflow/` → [raphael-nk/getaround-mlflow](https://huggingface.co/spaces/raphael-nk/getaround-mlflow)

**Space en ligne :** [https://raphael-nk-getaround-mlflow.hf.space](https://raphael-nk-getaround-mlflow.hf.space)

```
mlflow/                         # git submodule
├── Dockerfile                  # MLflow server 3.x, Python 3.11
├── entrypoint.sh               # mlflow server (backend Postgres + S3)
├── requirements.txt
├── README.md                   # frontmatter HF (sdk: docker)
└── .gitattributes
```

### Submodule `dashboard/` → [raphael-nk/getaround-dashboard](https://huggingface.co/spaces/raphael-nk/getaround-dashboard)

**Space en ligne :** [https://raphael-nk-getaround-dashboard.hf.space](https://raphael-nk-getaround-dashboard.hf.space)

```
dashboard/                      # git submodule
├── Dockerfile                  # Streamlit — sync S3 au démarrage
├── entrypoint.sh               # sync_data_from_s3.py puis streamlit
├── sync_data_from_s3.py        # télécharge datasets depuis GETAROUND_DATA_S3_URI
├── main.py                     # UI delay analysis + pricing + appels API
├── requirements.txt
├── README.md                   # variables HF + URI S3
├── users.json.dist             # template auth (copier → users.json en local)
├── assets/
│   └── logo.png
├── data/                       # optionnel en local (.gitignore sur le Space)
│   ├── get_around_delay_analysis.xlsx
│   └── get_around_pricing_project.csv
├── .gitignore                  # data/, users.json
└── .gitattributes
```

> **Note :** sur le Space HF, `dashboard/data/` n’est **pas** poussé dans Git (fichiers binaires). En production, les datasets viennent de **`s3://amzn-jedha-39/datasets/getaround/`** via `sync_data_from_s3.py`.

Le monorepo ne stocke qu’un **pointeur de commit** (gitlink) par submodule ; le code déployé est celui des repos Spaces ci-dessus.

**Documentation détaillée :** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · [docs/JOURNAL.md](docs/JOURNAL.md)

---

## Submodules Git ↔ Hugging Face Spaces

Configuration dans [`.gitmodules`](.gitmodules) :

| Dossier | Space Hugging Face | URL Space (repo) | URL production |
|---------|-------------------|------------------|----------------|
| `mlflow/` | `raphael-nk/getaround-mlflow` | [huggingface.co/spaces/raphael-nk/getaround-mlflow](https://huggingface.co/spaces/raphael-nk/getaround-mlflow) | [raphael-nk-getaround-mlflow.hf.space](https://raphael-nk-getaround-mlflow.hf.space) |
| `api/` | `raphael-nk/getaround-api` | [huggingface.co/spaces/raphael-nk/getaround-api](https://huggingface.co/spaces/raphael-nk/getaround-api) | [raphael-nk-getaround-api.hf.space](https://raphael-nk-getaround-api.hf.space) |
| `dashboard/` | `raphael-nk/getaround-dashboard` | [huggingface.co/spaces/raphael-nk/getaround-dashboard](https://huggingface.co/spaces/raphael-nk/getaround-dashboard) | [raphael-nk-getaround-dashboard.hf.space](https://raphael-nk-getaround-dashboard.hf.space) |

Remote Git de chaque submodule (branche `main`) :

```ini
# .gitmodules (extrait)
[submodule "mlflow"]
    path = mlflow
    url = https://huggingface.co/spaces/raphael-nk/getaround-mlflow
[submodule "api"]
    path = api
    url = https://huggingface.co/spaces/raphael-nk/getaround-api
[submodule "dashboard"]
    path = dashboard
    url = https://huggingface.co/spaces/raphael-nk/getaround-dashboard
```

### Cloner le projet complet

```bash
git clone --recurse-submodules <url-du-repo>
cd projet-getaround-bloc5
```

Si le dépôt est déjà cloné sans submodules :

```bash
git submodule update --init --recursive
```

### Modifier un service déployé

```bash
cd mlflow   # ou api / dashboard
# … éditer, commit …
git push origin main

cd ..
git add mlflow   # ou api / dashboard
git commit -m "Bump mlflow submodule"
git push
```

---

## Prérequis

- **Python** ≥ 3.12
- **[uv](https://docs.astral.sh/uv/)** (gestionnaire de dépendances) — groupes : `notebook`, `api`, `mlflow`, `dashboard`
- **pandas 2.x** (MLflow 3 n’est pas compatible avec pandas 3)
- **Git** avec support submodules
- **Docker** + **Docker Compose** *(optionnel)* — stack locale des 3 services
- Données dans `data/` à la racine (notebooks) ou accès S3 pour le dashboard
- **MLflow** : PostgreSQL (Neon) + artefacts S3 — voir `.env`
- **AWS** : lecture du bucket datasets pour le dashboard en prod (`GETAROUND_DATA_S3_URI`)

---

## Installation locale

```bash
git clone --recurse-submodules <url-du-repo>
cd projet-getaround-bloc5

uv sync
cp .env.dist .env
# Éditer .env (MLflow, AWS, GETAROUND_API_URL, GETAROUND_DATA_S3_URI, …)

cp dashboard/users.json.dist dashboard/users.json
# Éditer dashboard/users.json si besoin (connexion Streamlit)
```

---

## Docker Compose (stack locale)

Le fichier [`docker-compose.yml`](docker-compose.yml) démarre les **3 submodules** sur un réseau Docker partagé, avec healthchecks et ordre de démarrage (`mlflow` → `api` → `dashboard`).

### Lancer la stack

```bash
git clone --recurse-submodules <url-du-repo>
cd projet-getaround-bloc5
cp .env.dist .env
# Éditer .env (Postgres Neon, AWS, ARTIFACT_ROOT, …)

docker compose up --build
```

| Service | URL depuis votre machine |
|---------|--------------------------|
| MLflow | [http://127.0.0.1:5000](http://127.0.0.1:5000) |
| API (Swagger) | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |
| Dashboard | [http://127.0.0.1:8501](http://127.0.0.1:8501) |

Le dossier local **`data/`** est monté en lecture seule dans le dashboard (`./data:/app/data`), ce qui évite le sync S3 au démarrage.

### Variables d’environnement : hôte vs conteneurs

Le fichier **`.env`** à la racine est chargé par `api` et `dashboard` (`env_file`). Les URLs `http://127.0.0.1:…` conviennent au **développement hors Docker** (notebooks, `uvicorn` local).

**À l’intérieur des conteneurs**, `127.0.0.1` désigne le conteneur lui-même, pas les autres services. `docker-compose.yml` **surcharge** donc les variables lues par le code :

| Service | Variable lue par le code | Valeur dans Compose (réseau Docker) |
|---------|-------------------------|-------------------------------------|
| `api` | `MLFLOW_SERVER_URI` | `http://mlflow:5000` |
| `api` | `MLFLOW_PRODUCTION_RUN_NAME` | `production-best-model` |
| `dashboard` | `GETAROUND_API_URL` | `http://api:8000` |

Ne pas utiliser `MLFLOW_TRACKING_URI` ni `API_URL` dans Compose : l’API lit `MLFLOW_SERVER_URI` ([`api/main.py`](api/main.py)), le dashboard lit `GETAROUND_API_URL` ([`dashboard/main.py`](dashboard/main.py)).

Conserver dans **`.env`** :

```bash
MLFLOW_SERVER_URI=http://127.0.0.1:5000      # notebooks, dev local
GETAROUND_API_URL=http://127.0.0.1:8000
MLFLOW_PRODUCTION_RUN_NAME=production-best-model
```

### Vérification

```bash
curl -s http://127.0.0.1:8000/health | jq .
# Attendu : "model_loaded": true, "model_source": "mlflow" ou "local"
```

Le dashboard doit afficher l’API comme accessible (section statut de l’API de prédiction). Si `model_loaded` est `false`, vérifier le run MLflow `production-best-model` (ou tag `stage=production`) et les credentials **`AWS_*`** pour les artefacts S3.

---

## Configuration (`.env`)

Copier `.env.dist` vers `.env` et renseigner :

| Variable | Description |
|----------|-------------|
| `MLFLOW_BACKEND_STORE_URI` | URI Postgres pour le backend MLflow **server** |
| `MLFLOW_SERVER_URI` | URL HTTP du tracking client / API (prod : `https://raphael-nk-getaround-mlflow.hf.space`, local : `http://127.0.0.1:5000`) |
| `MLFLOW_EXPERIMENT` | Nom de l’expérience (défaut : `getaround-pricing`) |
| `MLFLOW_PRODUCTION_RUN_ID` | *(optionnel)* Forcer un run production précis |
| `MLFLOW_PRODUCTION_RUN_NAME` | *(optionnel)* Nom du run (défaut : `production-best-model`) |
| `ARTIFACT_ROOT` | Racine artefacts MLflow (`s3://...`) |
| `MLFLOW_S3_ENDPOINT_URL` | Endpoint S3 (ex. `https://s3.eu-west-3.amazonaws.com`) |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_DEFAULT_REGION` | Credentials AWS (MLflow artefacts + sync dashboard) |
| `GETAROUND_API_URL` | API pricing (prod : `https://raphael-nk-getaround-api.hf.space`, local : `http://127.0.0.1:8000` ; **Compose** surcharge en `http://api:8000`) |
| `GETAROUND_DATA_S3_URI` | Préfixe S3 datasets dashboard : `s3://amzn-jedha-39/datasets/getaround/` |
| `DATA_DIR` | *(optionnel)* Forcer le dossier data du dashboard ; Compose fixe `/app/data` pour le dashboard |

**Docker Compose :** `MLFLOW_SERVER_URI` et `GETAROUND_API_URL` du `.env` sont remplacés par les hostnames de service (`mlflow`, `api`) — voir [Docker Compose](#docker-compose-stack-locale).

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

Build depuis le dossier **`mlflow/`** (submodule, contexte = ce dossier) :

```bash
cd mlflow
docker build -t getaround-mlflow:latest .
docker run --rm -p 5000:5000 --env-file ../.env getaround-mlflow:latest
```

**Variables Space HF** (Settings → Variables and secrets) : `MLFLOW_BACKEND_STORE_URI`, `ARTIFACT_ROOT`, `AWS_*`, `MLFLOW_S3_ENDPOINT_URL`. Port : **`$PORT`** (7860 sur HF, 5000 en local).

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

Build depuis le dossier **`api/`** (submodule) :

```bash
cd api
docker build -t getaround-api:latest .
docker run --rm -p 7860:7860 --env-file ../.env getaround-api:latest
```

**Variables Space HF** : `MLFLOW_SERVER_URI=https://raphael-nk-getaround-mlflow.hf.space`, `MLFLOW_EXPERIMENT`, `MLFLOW_PRODUCTION_RUN_NAME`, `AWS_*` (chargement modèle depuis MLflow + S3). Pas de `.pkl` requis sur HF si le run production est disponible.

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

**Données :** en local, `dashboard/data/` puis `data/` à la racine. Sur le **Space dashboard HF**, les fichiers ne sont pas dans Git : ils sont téléchargés depuis **`GETAROUND_DATA_S3_URI`** au démarrage via `sync_data_from_s3.py`.

**Variables Space HF (dashboard)** — détail dans [`dashboard/README.md`](dashboard/README.md) :

| Variable | Description |
|----------|-------------|
| `GETAROUND_DATA_S3_URI` | `s3://amzn-jedha-39/datasets/getaround/` |
| `GETAROUND_API_URL` | `https://raphael-nk-getaround-api.hf.space` |
| `AWS_*` | Lecture S3 (secrets pour clés) |
| `PORT` | `7860` |

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
| **Dashboard** | [https://raphael-nk-getaround-dashboard.hf.space](https://raphael-nk-getaround-dashboard.hf.space) |
| **API** | [https://raphael-nk-getaround-api.hf.space](https://raphael-nk-getaround-api.hf.space) |
| **Documentation API** | [https://raphael-nk-getaround-api.hf.space/docs](https://raphael-nk-getaround-api.hf.space/docs) |
| **Health API** | [https://raphael-nk-getaround-api.hf.space/health](https://raphael-nk-getaround-api.hf.space/health) |
| **Predict** | [https://raphael-nk-getaround-api.hf.space/predict](https://raphael-nk-getaround-api.hf.space/predict) |
| **MLflow** | [https://raphael-nk-getaround-mlflow.hf.space](https://raphael-nk-getaround-mlflow.hf.space) |

**Exemple `POST /predict` (production) :**

```bash
curl -i -H "Content-Type: application/json" -X POST \
  -d '{"input":[{"model_key":"Citroën","mileage":50000,"engine_power":90,"fuel":"diesel","paint_color":"black","car_type":"hatchback","private_parking_available":true,"has_gps":true,"has_air_conditioning":true,"automatic_car":false,"has_getaround_connect":true,"has_speed_regulator":true,"winter_tires":false}]}' \
  https://raphael-nk-getaround-api.hf.space/predict
```

---

## Données

### Local (notebooks & dev)

Placer à la racine du monorepo dans **`data/`** :

1. **Delay Analysis** → `get_around_delay_analysis.xlsx`
2. **Pricing Optimization** → `get_around_pricing_project.csv`

### Production (dashboard sur Hugging Face)

Les binaires ne sont **pas** dans le repo Git du Space (rejet HF). Ils sont hébergés sur **S3** :

**`s3://amzn-jedha-39/datasets/getaround/`**

Au démarrage du conteneur dashboard, `sync_data_from_s3.py` télécharge les deux fichiers vers `/app/data`. Configurer **`GETAROUND_DATA_S3_URI`** et les credentials **`AWS_*`** dans les secrets du Space.

En local, le dashboard résout les chemins dans cet ordre : `dashboard/data/` → `data/` (racine) → variable **`DATA_DIR`**.

---

## Stack technique

- **Python 3.12** · **uv**
- **Pandas** · **scikit-learn** · **XGBoost** · **Optuna**
- **FastAPI** · **Uvicorn**
- **Streamlit**
- **MLflow 3.12** (tracking + artefacts S3) — voir [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) et [docs/JOURNAL.md](docs/JOURNAL.md)
- **PostgreSQL** (Neon) · **boto3** (artefacts MLflow + sync datasets dashboard)
- **Docker Compose** — stack locale (`docker-compose.yml`)
- **Hugging Face Spaces** (Docker) — déploiement API, MLflow, dashboard

---

## Auteur

**RANJAKASOA Raphaël Marcellin**

Projet réalisé dans le cadre du **Bloc 5 — Deployment**, certification **CDSD**, **Jedha Bootcamp**.

---

*GetAround × Jedha — 2026*
