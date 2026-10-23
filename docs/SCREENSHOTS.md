# Capturas de pantalla / Screenshots

Añade aquí capturas **reales** de la versión actual. No uses mockups o imágenes generadas para representar resultados que la aplicación no haya producido.

## Capturas recomendadas

Guarda las imágenes en `docs/screenshots/` con estos nombres sugeridos:

1. `dashboard.png` — pantalla principal de la aplicación.
2. `csv-upload.png` — carga de los CSV de demostración, si esa función está disponible.
3. `reconciliation-results.png` — resultado de una ejecución con discrepancias conocidas.
4. `run-history.png` — historial de ejecuciones, solo si está disponible y contiene datos de demostración.
5. `api-swagger.png` — documentación Swagger de la API.

## Cómo capturarlas en Windows

1. Abre la aplicación en el navegador.
2. Carga únicamente los CSV ficticios del proyecto.
3. Ejecuta la acción que deseas documentar y comprueba el resultado.
4. Usa `Win + Shift + S` para seleccionar el área.
5. Guarda la imagen con el nombre correspondiente dentro de `docs/screenshots/`.
6. Oculta o evita cualquier dato personal, credencial, token o cadena de conexión.

## Cómo insertarlas en el README

Cuando exista el archivo, puedes enlazarlo desde `README.md`, por ejemplo:

```markdown
![Resultado de reconciliación](docs/screenshots/reconciliation-results.png)
```

No añadas referencias a imágenes hasta que esos archivos existan en el repositorio.
