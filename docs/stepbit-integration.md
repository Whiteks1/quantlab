# Integración con Stepbit-core

Este documento describe la arquitectura y los casos de uso para integrar **QuantLab** con **Stepbit-core**, un sistema operativo de IA local-first. Esta unión permite que la investigación cuantitativa sea guiada por inteligencia artificial autónoma.

## 1. Arquitectura de Conexión

La integración se realiza a través de la capa **MCP (Model Context Protocol)** de Stepbit-core, que trata a QuantLab como una "herramienta" especializada.

### Flujo de Trabajo
1.  **Orquestador (Stepbit)**: Recibe un objetivo (ej: "Optimizar estrategia X").
2.  **Herramienta QuantLab (MCP)**: Llama a `main.py` de QuantLab con los parámetros generados por la IA.
3.  **Ejecución (QuantLab)**: Procesa el backtest o la ingesta de datos y genera un `report.json`.
4.  **Análisis (Stepbit)**: Lee el JSON, analiza las métricas y decide el siguiente paso o entrega el resultado final.

## 2. Requisitos Técnicos en QuantLab

Para que esta integración sea robusta, el repositorio de QuantLab debe cumplir con:
- **Salida JSON Estable**: El comando `--report` debe generar siempre un archivo `report.json` con métricas clave (Sharpe, Drawdown, Win Rate).
- **Interfaz CLI**: Mantener la compatibilidad de flags en `main.py` para permitir la automatización por subprocesos.
- **Entorno Virtual**: Uso consistente de `.venv` para que Stepbit pueda invocar el intérprete correcto.

## 3. Casos de Uso Principales

### A. Optimización Autónoma (Estratega IA)
La IA realiza grid-searches inteligentes, analizando no solo el retorno final sino la calidad de los trades reportados por QuantLab.

### B. Notificaciones de Inflexión (Eventos)
QuantLab puede actuar como un emisor de eventos. Si un script de monitoreo detecta una señal, Stepbit puede disparar flujos de trabajo de análisis de riesgo complejos.

### C. Investigación Distribuida
Uso de los nodos de Stepbit para paralelizar sweeps de parámetros masivos, ejecutando múltiples instancias de QuantLab de forma coordinada.

## 4. Roadmap de Integración
- [ ] Creación de `QuantLabTool.rs` en Stepbit-core.
- [ ] Pruebas de ejecución de backtest desde el Reasoning Engine.
- [ ] Implementación de triggers basados en eventos de QuantLab.
