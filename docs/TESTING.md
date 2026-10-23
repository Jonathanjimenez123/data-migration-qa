# Pruebas y validación / Testing and validation

## Pruebas automatizadas de la API

En la configuración local utilizada durante el desarrollo, se ejecutaron las pruebas con:

```powershell
Set-Location "C:\data-migration-qa"
$env:PYTHONPATH="$PWD\apps\api"
& ".\apps\api\.venv\Scripts\python.exe" -m pytest -q apps\api\tests
```

El resultado registrado en una sesión anterior fue **15 pruebas aprobadas y 1 advertencia**. Es un resultado histórico, no una garantía de que las pruebas actuales sigan pasando. Vuelve a ejecutar el comando antes de publicar cambios y documenta el resultado real.

## Compilación del frontend

```powershell
Set-Location "C:\data-migration-qa\apps\web"
npm run build
```

La compilación también había terminado correctamente en una sesión anterior. Vuelve a ejecutarla tras modificar el frontend.

## Prueba manual de reconciliación

Usa CSV ficticios con columnas compatibles con la interfaz. Un escenario de demostración previamente utilizado contenía:

- Un registro presente en el origen y ausente en el destino.
- Un registro presente en el destino y ausente en el origen.
- Un valor de saldo diferente para una clave que existe en ambos conjuntos.

Comprueba que la interfaz identifique las discrepancias correctas según los datos cargados. No asumas que los resultados son correctos únicamente porque la ejecución termina: compara el resultado con el contenido de los CSV.

## Lista de verificación antes de publicar

- [ ] Las pruebas automatizadas terminan correctamente.
- [ ] `npm run build` termina correctamente.
- [ ] La reconciliación manual identifica las diferencias esperadas.
- [ ] Los endpoints desplegados responden según lo esperado.
- [ ] No se muestran secretos ni datos reales en logs, capturas o CSV.
- [ ] Se revisan los archivos staged antes de hacer commit.
