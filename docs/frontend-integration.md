# Integración del Frontend: Stepbit UI + QuantLab

Es totalmente posible (y muy recomendado) integrar **QuantLab** en la interfaz visual de **Stepbit**. Esto permitiría pasar de una experiencia puramente CLI a un panel de control de investigación cuantitativa.

## 1. Arquitectura de Conexión UI

La interfaz de Stepbit está construida con **React + Vite** y se comunica con un backend en **Rust (Actix-web)** que actúa como gateway.

### Flujo de Datos
1.  **Backend Proxy**: El servidor `stepbit` (en `/api/quantlab/*`) servirá los archivos estáticos (gráficos `.png`) y los datos JSON de la carpeta `quantlab/outputs/`.
2.  **Frontend State**: Se añadirá un nuevo servicio en la capa de API de React (`src/api/quantlab.ts`) para consultar los experimentos.
3.  **Visualización**: React renderizará las curvas de equity y los reportes de métricas.

## 2. Componentes Propuestos para la UI

### A. QuantLab Explorer (Nueva Página)
Una vista dedicada con:
- **Listado de Ejecuciones**: Una tabla o grid con todos los backtests realizados, mostrando el Sharpe Ratio y ROI de un vistazo.
- **Visor de Artefactos**: Al hacer clic en una ejecución, se muestran los gráficos de `equity.png` y `price_signals.png` generados por QuantLab.
- **Comparador**: Una herramienta para seleccionar dos "runs" y ver sus métricas comparadas.

### B. Widget de Estratega (Reasoning Playground)
Integración con la consola de IA:
- Cuando la IA lanza un backtest, el progreso se puede ver en tiempo real.
- Los resultados aparecen como "cards" interactivas dentro del chat que puedes expandir para ver el detalle técnico.

## 3. Pasos para la Implementación

1.  **Exponer Artefactos**: Modificar `stepbit/src/main.rs` (el backend del frontend) para servir la carpeta `quantlab/outputs/` como una ruta de archivos estáticos.
2.  **Crear `QuantLab.tsx`**: Crear la página en `stepbit/frontend/src/pages/` siguiendo el patrón estético del resto de la aplicación (vibrante, modo oscuro, premium).
3.  **Vínculo con McpTools**: Añadir un botón rápido en la página de **MCP Tools** para "Lanzar Backtest" que abra un modal con parámetros predefinidos.

## 4. Ventaja Competitiva
Al conectar ambos frontends, el usuario puede **razonar con la IA en una ventana** mientras **ve los resultados visuales de su estrategia en la otra**, creando un ciclo de feedback inmediato para la exploración de mercados.
