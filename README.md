# Proyecto Frontier Back

Backend en FastAPI para Proyecto Frontier.

Usa los JSON copiados desde el frontend como fuente temporal de datos mientras no exista una base de datos real. Se han ignorado los JSON de Pokemon y Pixelmon, tal como pediste.

El modelo se ha normalizado para soportar que un equipo pueda participar en varias temporadas y que su plantilla cambie por liga y temporada.

## Estructura

```text
app/
  api/v1/endpoints/   -> routers por recurso
  core/               -> configuracion global
  models/             -> modelos internos de dominio
  repositories/       -> acceso a datos JSON
  schemas/            -> contratos de entrada y salida
  services/           -> logica de negocio
data/                 -> datos simulando la BBDD
```

## Datos usados

- `data/leagues_data.json`
- `data/season_data.json`
- `data/players_data.json`
- `data/inazuma_characters.json`
- `data/teams_data.json`
- `data/elements_img.json`
- `data/gender_img.json`

## Modelo de datos

- `leagues_data.json`: catalogo de ligas
- `season_data.json`: temporadas ligadas a una liga
- `teams_data.json`: entidad base del equipo y sus participaciones (`id_league` + `id_season`)
- `players_data.json`: plantilla por equipo, liga y temporada
- `inazuma_characters.json`: catalogo maestro de personajes

## Instalacion

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Arranque

```bash
uvicorn app.main:app --reload
```

## Documentacion

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Endpoints principales

- `GET /api/v1/health`
- `GET /api/v1/leagues`
- `GET /api/v1/seasons`
- `GET /api/v1/players`
- `GET /api/v1/players/{player_id}`
- `GET /api/v1/teams`
- `GET /api/v1/teams/{team_id}`
- `GET /api/v1/teams/{team_id}/players`
- `GET /api/v1/metadata/elements`
- `GET /api/v1/metadata/genders`

## Filtros soportados

`GET /api/v1/players` acepta:

- `search`
- `active`
- `gender`
- `element`
- `position`
- `page`
- `page_size`

`GET /api/v1/teams` y `GET /api/v1/teams/{team_id}` aceptan:

- `league_id`
- `season_id`
- `include_players`

`GET /api/v1/teams/{team_id}/players` acepta:

- `league_id`
- `season_id`
- `include_coaches`
