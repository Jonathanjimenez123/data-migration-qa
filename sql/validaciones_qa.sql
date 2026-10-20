
-- DATA MIGRATION QA: VALIDACIONES AUTOMATIZADAS

-- 1. Comparar cantidad de registros
SELECT
    'TOTAL_REGISTROS' AS prueba,
    CASE
        WHEN (SELECT COUNT(*) FROM origen_aws) =
             (SELECT COUNT(*) FROM destino_postgresql)
        THEN 'PASS'
        ELSE 'FAIL'
    END AS resultado,
    (SELECT COUNT(*) FROM origen_aws) AS total_origen,
    (SELECT COUNT(*) FROM destino_postgresql) AS total_destino;

-- 2. Detectar registros faltantes en destino
SELECT
    'REGISTRO_FALTANTE' AS prueba,
    o.id,
    o.nombre
FROM origen_aws o
LEFT JOIN destino_postgresql d ON d.id = o.id
WHERE d.id IS NULL;

-- 3. Detectar registros inesperados en destino
SELECT
    'REGISTRO_INESPERADO' AS prueba,
    d.id,
    d.nombre
FROM destino_postgresql d
LEFT JOIN origen_aws o ON o.id = d.id
WHERE o.id IS NULL;

-- 4. Detectar diferencias de saldo
SELECT
    'SALDO_DIFERENTE' AS prueba,
    o.id,
    o.saldo AS saldo_origen,
    d.saldo AS saldo_destino
FROM origen_aws o
JOIN destino_postgresql d ON d.id = o.id
WHERE o.saldo IS DISTINCT FROM d.saldo;

-- 5. Detectar emails vacíos o nulos
SELECT
    'EMAIL_INVALIDO' AS prueba,
    id,
    nombre,
    email
FROM destino_postgresql
WHERE email IS NULL OR BTRIM(email) = '';

