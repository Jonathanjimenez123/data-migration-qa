# Data Migration QA

**Herramienta de portafolio para validar y reconciliar datos entre sistemas de origen y destino.**

Data Migration QA es un proyecto personal orientado a QA de datos y automatización de pruebas. Permite comparar conjuntos de datos, identificar discrepancias y consultar resultados desde una interfaz web y una API.

> Proyecto demostrativo. Utiliza datos ficticios; no está destinado a procesar datos financieros o personales reales sin una evaluación adicional de seguridad y requisitos.

## Demo y enlaces

- **Aplicación web:** https://data-migration-qa.vercel.app/
- **API:** https://data-migration-qa-api.onrender.com/
- **Documentación interactiva de la API:** https://data-migration-qa-api.onrender.com/docs
- **Health check:** https://data-migration-qa-api.onrender.com/api/v1/health
- **Código fuente:** https://github.com/Jonathanjimenez123/data-migration-qa

Los servicios gratuitos pueden tardar unos momentos en responder después de estar inactivos.

## ¿Qué problema aborda?

Durante una migración de datos, los registros pueden faltar, aparecer de más o contener valores diferentes entre el origen y el destino. El proyecto busca hacer visibles esas diferencias mediante verificaciones repetibles.

## Funcionalidades

- Comparación de datos de origen y destino.
- Detección de registros faltantes e inesperados.
- Identificación de diferencias en campos.
- Visualización de resultados de reconciliación.
- API REST con documentación Swagger/OpenAPI.
- Pruebas automatizadas para la API.
- Despliegue de la interfaz y la API en servicios web independientes.

La disponibilidad de cada verificación depende de la configuración y la versión desplegada.

## Tecnologías

| Área | Tecnología |
|---|---|
| Interfaz | React, Vite, JavaScript |
| API | Python, FastAPI |
| Base de datos | PostgreSQL |
| Pruebas | pytest |
| Frontend desplegado en | Vercel |
| API desplegada en | Render |
| Base de datos administrada | Neon PostgreSQL |

## Arquitectura

```text
Usuario
  |
  v
Interfaz React + Vite (Vercel)
  |
  v
API REST FastAPI (Render)
  |
  v
PostgreSQL administrado (Neon)
```

Consulta [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) para más información.

## Probar la demo

1. Abre la [aplicación web](https://data-migration-qa.vercel.app/).
2. Carga archivos CSV de demostración si la interfaz ofrece esa opción.
3. Ejecuta la reconciliación.
4. Revisa los registros coincidentes y las diferencias que muestre el resultado.

Los CSV de ejemplo deben ser ficticios. Revisa las columnas que espera la interfaz antes de cargar archivos propios.

## Ejecución local

### Requisitos

- Git
- Node.js y npm
- Python compatible con las dependencias del proyecto
- PostgreSQL si vas a ejecutar las funciones que requieren base de datos

### Frontend

Desde PowerShell:

```powershell
Set-Location "C:\data-migration-qa\apps\web"
npm install
npm run dev
```

Para validar la compilación de producción:

```powershell
npm run build
```

### API y pruebas

En el repositorio, desde la carpeta raíz, activa primero el entorno virtual de Python si ya existe. En la configuración local utilizada para este proyecto, las pruebas se ejecutaron así:

```powershell
Set-Location "C:\data-migration-qa"
$env:PYTHONPATH="$PWD\apps\api"
& ".\apps\api\.venv\Scripts\python.exe" -m pytest -q apps\api\tests
```

Este comando presupone que el entorno virtual está creado en `apps\api\.venv` y que las dependencias están instaladas. Si estás configurando el proyecto en otro equipo, consulta los archivos de dependencias del repositorio y la configuración de la API.

## Documentación adicional

- [Arquitectura](docs/ARCHITECTURE.md)
- [Pruebas](docs/TESTING.md)
- [Capturas de pantalla](docs/SCREENSHOTS.md)
- [English README](README.en.md)

## Capturas

Las capturas reales de la aplicación se añadirán en `docs/screenshots/`. Consulta [`docs/SCREENSHOTS.md`](docs/SCREENSHOTS.md). No se incluyen imágenes simuladas como si fueran capturas del sistema.

## Seguridad y datos

- No publiques archivos `.env`, contraseñas, claves, tokens ni cadenas de conexión.
- No uses datos personales o financieros reales en capturas, CSV de demostración o reportes públicos.
- Mantén las credenciales en las variables de entorno de cada servicio.
- Antes de publicar cambios, revisa `git status` y los archivos que vas a incluir en el commit.

## Sobre el proyecto

Proyecto personal de portafolio creado para practicar validación de datos, pruebas automatizadas, desarrollo de API y despliegue web. Los resultados y capacidades deben evaluarse con la versión actual del código y las pruebas ejecutadas; no se presentan como experiencia laboral remunerada.
