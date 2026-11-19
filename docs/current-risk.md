# Riesgo estimado hoy

**Qué es:** una estimación de ESCUDO, de 0 a 100, que indica en qué municipios coinciden hoy territorio de riesgo oficial alto y tiempo previsto favorable al fuego.

**Qué no es:** no es un dato oficial de AEMET ni de la Comunidad de Madrid, ni una probabilidad de incendio, ni una alerta. No sustituye al mapa de peligro de AEMET ni a los avisos oficiales.

## Fórmula

`riesgo estimado = 100 × territorio × meteorología`

| Factor | Cálculo | Fuente |
|---|---|---|
| Territorio (0–1) | Parte del término en las clases 4 y 5 del mapa oficial, suma literal | GEO-01 |
| Meteorología (0–1) | Máximo de las próximas 24 horas del índice de Fosberg, dividido entre 100, solo en horas anteriores a la lluvia | AEMET-PRED-HOR |

El producto evita elegir pesos y exige que coincidan los dos factores: mucho viento sobre un término sin riesgo alto no da un valor alto, ni tampoco un término de riesgo alto con tiempo húmedo y en calma.

**Tramos fijos:** muy alto ≥ 80, alto ≥ 60, moderado ≥ 40, bajo ≥ 20, muy bajo < 20. Son una decisión de ESCUDO.

## Índice de Fosberg

Fosberg, M. A. (1978), *Weather in wildland fire management: the fire weather index*. `T` en °F, `h` en %, `U` en mph (viento medio):

```text
h < 10:        m = 0,03229 + 0,281073·h − 0,000578·h·T
10 ≤ h ≤ 50:   m = 2,22749 + 0,160107·h − 0,01478·T
h > 50:        m = 21,0606 + 0,005565·h² − 0,00035·h·T − 0,483199·h
η = 1 − 2(m/30) + 1,5(m/30)² − 0,5(m/30)³
FFWI = η · √(1 + U²) / 0,3002, acotado entre 0 y 100
```

## Lluvia prevista

Fosberg no incluye la lluvia, de modo que un temporal húmedo con viento fuerte daría un valor alto. Por eso el índice deja de contar desde la hora en que la lluvia prevista acumulada alcanza **0,5 mm**. Si ocurre en la primera hora, el factor meteorológico es 0. El umbral es una decisión de ESCUDO; toma como referencia los 0,5 mm que el código canadiense de humedad del combustible fino descuenta de la lluvia diaria (Van Wagner, 1987).

## Límites

- Solo usa el tiempo previsto. No conoce el estado real de la vegetación, la sequía ni la lluvia ya caída.
- El índice se desarrolló en Estados Unidos y **no se ha calibrado ni validado con incendios de Madrid**.
- La predicción es para el término municipal, no para una urbanización concreta.
- Sin predicción vigente o sin capa oficial el resultado es `null`. No se reutiliza una predicción caducada.
