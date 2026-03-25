# Workflow Operativo Para Trabajar En `quant_lab`

Este documento define la forma recomendada de trabajar dentro de `quant_lab` cuando se colabora con Codex u otros asistentes de ejecución.

Su objetivo es mantener el repositorio ordenado, la historia Git legible y la autoridad del sistema dentro de QuantLab.

## 1. Definir el tipo de trabajo

Antes de tocar archivos, clasificar la tarea en una de estas categorías:

- `runtime fix`
- `docs / roadmap / arquitectura`
- `contrato público`
- `tests / hardening`
- `paper trading`
- `broker / safety`
- `integración externa`

Regla:

- si la tarea afecta comportamiento real, primero validar el runtime
- si la tarea afecta narrativa, roadmap o arquitectura, primero validar autoridad y alcance

## 2. Confirmar el repo correcto

Antes de trabajar, comprobar siempre:

- que estamos dentro del repo `quant_lab`
- rama actual
- estado del árbol
- existencia de archivos sueltos no relacionados

Reglas:

- no trabajar desde la carpeta paraguas
- no tocar otros repos salvo revisión explícita
- no incluir archivos sueltos como `main.cpp` sin decisión explícita

## 3. Aclarar alcance antes de implementar

Antes de hacer un cambio sustancial:

- listar los archivos o superficies que se van a tocar
- marcar supuestos
- señalar riesgos o decisiones no obvias
- validar el alcance antes de arrancar implementación grande

Regla:

- no abrir trabajo grande sin ese pequeño contrato previo

## 4. Ejecutar en este orden

Orden base recomendado:

1. fix de superficie pública si algo está roto
2. estado interno en `.agents/`
3. contrato público
4. tests relevantes
5. documentación pública
6. backlog / issues
7. limpieza de ramas si toca

Reglas:

- no documentar una superficie pública rota
- no tocar backlog antes de entender el estado real del código

## 5. Mantener `quant_lab` como sistema soberano

Principio rector:

- `quant_lab` manda sobre su roadmap, contratos, riesgo y operación
- integraciones externas solo justifican cambios si mejoran la frontera sin comprometer autonomía

Filtro para cambios motivados por Stepbit:

- mejora la frontera externa
- no mueve autoridad fuera de QuantLab
- sigue siendo reversible

## 6. Tratar Stepbit como consumidor externo

Para `stepbit-core` o `stepbit-app`:

- no hacer cambios de código ahí salvo petición explícita
- revisar integración solo si hace falta para entender la frontera
- cualquier necesidad o follow-up se devuelve como issue

Regla:

- siempre incluir `labels` cuando se propongan issues

## 7. Hacer cambios cohesivos

Norma de implementación:

- cambios pequeños y cerrables
- una intención por rama
- commits separados si se mezclan runtime y docs
- evitar refactors amplios si no son necesarios

Convención:

- las ramas nuevas deben usar el prefijo `codex/`

## 8. Verificar siempre

Después de implementar:

- correr checks focalizados
- dejar claro qué se validó
- señalar explícitamente qué no se pudo validar

Tipos típicos de verificación:

- comandos CLI
- tests concretos
- diff de contrato
- revisión de artefactos reales

## 9. Preparar salida profesional

Al cerrar una tanda:

- dejar la rama limpia
- preparar commit o commits coherentes
- hacer push solo si se pide
- entregar texto de PR
- si hay impacto en otros repos, redactar issues bien formuladas y con `labels`

## 10. Cerrar y dejar base limpia

Al final:

- volver a `main` cuando proceda
- limpiar ramas mergeadas si toca
- no arrastrar archivos no relacionados
- dejar claro cuál es el siguiente bloque lógico

## Orden estratégico actual de `quant_lab`

A día de hoy, el orden correcto es:

1. `Stage C.1 - Paper Trading Operationalization`
2. hardening puntual de frontera externa solo si hay fricción real
3. `Stage D.0 - Real Execution Safety Boundary`
4. broker dry-run
5. sandbox / simulación
6. live supervisado
7. automatización controlada

Interpretación:

- Stepbit no dicta el roadmap de QuantLab
- la frontera externa se mejora cuando ayuda, no cuando desplaza prioridades soberanas

## Autoridad documental

Para evitar contradicciones entre capas:

- `docs/` contiene la guía pública y estable del repositorio
- `.agents/` contiene continuidad operativa interna y contexto de ejecución
- si aparece una contradicción, primero se corrige el estado real y luego se alinean ambas capas

## Reglas rápidas

- no tocar `stepbit` sin motivo claro
- no dejar que Stepbit dicte el roadmap de QuantLab
- no documentar cosas rotas
- no mezclar cambios de distinta naturaleza si complica la historia Git
- no abrir trabajo grande sin una lista previa de alcance
- siempre con `labels` cuando haya issues
