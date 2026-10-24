# Data Migration QA

Proyecto personal de portafolio para validar, comparar y reconciliar datos entre sistemas de origen y destino mediante una aplicación web, una API y pruebas automatizadas.

## Enlaces

- **Aplicación web:** https://data-migration-qa.vercel.app/
- **API:** https://data-migration-qa-api.onrender.com/
- **Documentación de la API:** https://data-migration-qa-api.onrender.com/docs
- **Estado de la API:** https://data-migration-qa-api.onrender.com/api/v1/health
- **Código fuente:** https://github.com/Jonathanjimenez123/data-migration-qa

## Objetivo

Demostrar habilidades prácticas en QA de datos, validación de migraciones, desarrollo de API y pruebas automatizadas.

## Funcionalidades

- Comparación de datos entre sistemas de origen y destino.
- Detección de registros faltantes e inesperados.
- Identificación de diferencias entre registros.
- Consulta de resultados e historial de ejecuciones.
- API para acceder a las funciones disponibles.
- Pruebas automatizadas con pytest.
- Datos de demostración para realizar validaciones.

## Tecnologías

- **Frontend:** React y Vite.
- **Backend:** Python y FastAPI.
- **Pruebas:** pytest.
- **Base de datos:** PostgreSQL.
- **Despliegue:** Vercel y Render.
- **Control de versiones:** Git y GitHub.

## Capturas de pantalla

### 1. Panel de control

![Panel de control](docs/screenshots/01-panel-control.png)

### 2. Detalle del panel

![Detalle del panel de control](docs/screenshots/02-panel-control-detalle.png)

### 3. Nueva reconciliación

![Nueva reconciliación](docs/screenshots/03-nueva-reconciliacion.png)

### 4. Historial de ejecuciones

![Historial de ejecuciones](docs/screenshots/04-historial-ejecuciones.png)

### 5. Calidad de datos

![Calidad de datos](docs/screenshots/05-calidad-de-datos.png)

## Ejecutar las pruebas

Si el entorno virtual y las dependencias ya están instalados, ejecuta:

```powershell
Set-Location "C:\data-migration-qa"
$env:PYTHONPATH="$PWD\apps\api"
& ".\apps\api\.venv\Scripts\python.exe" -m pytest -q apps\api\tests
```

Durante el desarrollo se registró una ejecución con 15 pruebas aprobadas. Ejecuta el comando anterior para verificar el estado actual.

## Documentación técnica

- [Arquitectura](docs/ARCHITECTURE.md)
- [Pruebas](docs/TESTING.md)

## Seguridad

- Utiliza únicamente datos ficticios en los ejemplos públicos.
- No publiques contraseñas, tokens, claves, archivos `.env` ni cadenas de conexión.
- Configura las credenciales mediante variables de entorno.

## Sobre el proyecto

Proyecto personal de aprendizaje y portafolio orientado a demostrar conocimientos prácticos en QA de datos, automatización de pruebas, Python, desarrollo web y API. No se presenta como experiencia laboral remunerada.