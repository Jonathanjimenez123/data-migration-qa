# Arquitectura / Architecture

## Componentes

1. **Frontend — React + Vite:** interfaz para interactuar con el proceso de reconciliación y consultar resultados.
2. **API — Python + FastAPI:** expone endpoints HTTP para las funciones disponibles y ofrece documentación OpenAPI/Swagger.
3. **Persistencia — PostgreSQL:** almacena información relacionada con ejecuciones y resultados de QA, según el esquema configurado.
4. **Despliegue:** Vercel sirve el frontend; Render ejecuta la API; Neon ofrece PostgreSQL administrado.

## Flujo de alto nivel

```text
Navegador
   |
   v
Frontend React (Vercel)
   |  solicitudes HTTP
   v
API FastAPI (Render)
   |
   v
PostgreSQL (Neon)
```

## Endpoints publicados

- API base: https://data-migration-qa-api.onrender.com/
- Swagger UI: https://data-migration-qa-api.onrender.com/docs
- Health check: https://data-migration-qa-api.onrender.com/api/v1/health

Consulta Swagger para confirmar los endpoints y los esquemas disponibles en la versión desplegada.

## Configuración y seguridad

La API utiliza variables de entorno para la configuración de conexión y origen permitido del frontend. Los valores secretos no deben escribirse en este documento ni subirse al repositorio. En producción, la conexión a PostgreSQL debe usar la configuración SSL requerida por el proveedor.

## Límites de esta descripción

Este documento describe la arquitectura de alto nivel conocida del proyecto. Los detalles de módulos, tablas, validaciones y endpoints deben contrastarse con el código actual antes de considerar este documento una especificación exhaustiva.
