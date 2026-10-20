
"""API principal de Data Migration QA."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.reconciliation import router as reconciliation_router
from app.routers.runs import router as runs_router


app = FastAPI(
    title="Data Migration QA",
    summary="Plataforma de reconciliación y calidad de datos",
    description=(
        "API para comparar archivos de origen y destino, detectar diferencias "
        "y generar resultados estructurados de calidad de datos."
    ),
    version="0.1.0",
)


# ---------------------------------------------------------
# CORS: DESARROLLO Y PRODUCCION
# ---------------------------------------------------------

local_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# En producción, configura FRONTEND_ORIGIN con el dominio
# real de Vercel. Se permiten varios dominios separados por comas.
configured_origins = os.getenv("FRONTEND_ORIGIN", "")

production_origins = [
    origin.strip().rstrip("/")
    for origin in configured_origins.split(",")
    if origin.strip()
]

allowed_origins = list(dict.fromkeys(
    local_origins + production_origins
))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# ---------------------------------------------------------
# RUTAS DEL SISTEMA
# ---------------------------------------------------------

@app.get("/", tags=["System"])
def root():
    """Devuelve información básica de la aplicación."""

    return {
        "application": "Data Migration QA",
        "version": app.version,
        "docs": "/docs",
        "health": "/api/v1/health",
    }


@app.get("/api/v1/health", tags=["System"])
def health():
    """Comprueba que la API está respondiendo."""

    return {
        "status": "ok",
        "application": "Data Migration QA",
        "version": app.version,
    }


# ---------------------------------------------------------
# ROUTERS
# ---------------------------------------------------------

app.include_router(reconciliation_router)
app.include_router(runs_router)

