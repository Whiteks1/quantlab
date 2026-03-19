# Casos de Uso Detallados: IA + QuantLab

La integración con **Stepbit-core** transforma a QuantLab de una herramienta de análisis pasivo a un laboratorio de investigación autónomo y reactivo.

## 1. El Estratega Autónomo (Búsqueda de Alfa)
**Objetivo**: Automatizar el proceso de prueba y error en el diseño de estrategias.
- **Flujo**:
    1. El usuario entrega una idea vaga: *"Quiero una estrategia de reversión a la media con RSI"*.
    2. El **Planner** de Stepbit genera una lista de parámetros candidatos (ej: RSI 10, 14, 21; periodos de MA 20, 50, 100).
    3. Stepbit invoca a QuantLab en bucle para ejecutar backtests de todas las combinaciones.
    4. El agente de IA analiza el `report.json` de cada ejecución, descartando aquellas con alto drawdown y seleccionando las de mayor Profit Factor.
    5. **Resultado**: Una recomendación final con parámetros optimizados y justificación estadística.

## 2. Guardián de Riesgo Dinámico (Vigilancia 24/7)
**Objetivo**: Reaccionar a condiciones de mercado en tiempo real sin intervención humana.
- **Flujo**:
    1. Un script de QuantLab (ej: `track_market.py`) vigila el precio.
    2. Al detectar un evento (ej: volatilidad extrema detectada por el ATR), envía un `SyncEvent` al **EventBus** de Stepbit.
    3. Stepbit tiene un **Trigger** configurado: si el evento es `market.volatility_high`, lanzar el Reasoning Graph de "Liquidación Gradual".
    4. La IA evalúa la posición actual del portfolio (vía `portfolio_report`) y decide si cerrar posiciones o mover el Stop Loss.

## 3. Generación de Reportes Ejecutivos mediante IA
**Objetivo**: Traducir métricas técnicas a lenguaje natural y decisiones de negocio.
- **Flujo**:
    1. QuantLab genera gráficas de equity y archivos JSON de métricas.
    2. Stepbit toma estos artefactos y los pasa por su motor de razonamiento junto con el contexto del mercado (noticias, sentimiento).
    3. **Resultado**: Un reporte Markdown diario en `outputs/daily_summary.md` que explica no solo *qué* pasó, sino *por qué* y si la estrategia sigue siendo válida según las condiciones actuales.

## 4. Backtesting Distribuido en el Cluster
**Objetivo**: Reducir el tiempo de optimización (Sweep) de horas a minutos.
- **Flujo**:
    1. El **Controller** de Stepbit divide una tarea de "Sweep" de 10,000 iteraciones en 10 bloques de 1,000.
    2. Envía cada bloque a un **Worker** diferente en la red local.
    3. Cada Worker ejecuta su instancia local de QuantLab.
    4. Los resultados se agregan en el Controller, que presenta la "frontera de eficiencia" consolidada.
