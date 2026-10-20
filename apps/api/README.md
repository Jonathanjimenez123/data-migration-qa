# Data Migration QA API

## Ejecución local

Desde PowerShell, en `C:\data-migration-qa`:

```powershell
.\apps\api\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir .\apps\api --host 127.0.0.1 --port 8000
```

Documentación interactiva: http://127.0.0.1:8000/docs

Estado: http://127.0.0.1:8000/api/v1/health

## Comparación de archivos

POST `/api/v1/reconciliation/files`

Campos multipart:
- `source_file`: CSV o XLSX de origen.
- `target_file`: CSV o XLSX de destino.
- `key_column`: nombre de la columna identificadora; por defecto `id`.

Límites iniciales:
- 10 MB por archivo.
- 100.000 filas por archivo.
- Archivos procesados en memoria, sin persistencia.

## Estado de seguridad

Esta versión es una API local de desarrollo, no una instalación lista para exposición pública. Antes de desplegarla se requiere autenticación, autorización, límites de concurrencia, controles de almacenamiento, auditoría y configuración segura de producción.
