# Workflow Operativo Para Trabajar En `quant_lab`

Este documento define la forma recomendada de trabajar dentro de `quant_lab` cuando se colabora con Codex u otros asistentes de ejecución.

Su objetivo es mantener el repositorio ordenado, la historia Git legible y la autoridad del sistema dentro de QuantLab.

## Contrato obligatorio para colaboradores

Este marco es obligatorio para cualquier colaborador externo, incluido un dev senior o un agente basado en Codex.

Reglas mínimas no negociables:

- el repo canónico y `origin/main` mandan
- nunca se hace push directo a `main`
- por defecto: `1 issue = 1 branch = 1 PR`
- una rama debe tener una sola historia técnica dominante
- no se trabaja desde ramas stale, huérfanas o con upstream `gone`
- si una rama pierde su upstream o deja de representar el estado real del repo, el siguiente trabajo arranca desde `origin/main`
- el colaborador puede proponer arquitectura, pero no redefinir roadmap, prioridades ni fronteras de ownership sin decisión explícita del owner del repo

Superficies de alto control que exigen preflight reforzado y ownership claro:

- `src/quantlab/brokers/hyperliquid.py`
- `src/quantlab/cli/hyperliquid_submit_sessions.py`
- `report.json.machine_contract`
- `--json-request`
- `desktop/main.js`
- `desktop/scripts/smoke.js`
- `.github/workflows/ci.yml`

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
- si la rama local no refleja el estado canónico del repo, detenerse y volver a una base limpia desde `origin/main`

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

## 7.1 Flujo obligatorio cuando hay diff real

Si una tarea deja un diff real, el flujo por defecto no termina en “cambio local hecho”.

La secuencia esperada es:

1. issue o task en alcance
2. rama dedicada
3. implementación acotada
4. comprobaciones correctas y focalizadas
5. commit o commits coherentes
6. PR real
7. merge
8. cierre del issue vinculado
9. limpieza de ramas y restos locales/remotos

Regla:

- no preguntar otra vez por cada paso rutinario si el usuario ya encargó la ejecución completa
- solo detenerse antes del siguiente paso si el usuario lo pide explícitamente o si el estado del repo/permisos lo bloquea

Esto incluye:

- no dejar ramas de trabajo abiertas sin motivo
- no dejar commits locales sueltos o historia confusa si la tanda ya está lista
- no dejar ramas remotas mergeadas sin limpiar cuando el flujo permita cerrarlas

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

Regla adicional:

- antes de commit, PR o merge, debe quedar claro qué comprobaciones se ejecutaron y si fueron suficientes para la surface tocada
- si no se pudo validar una surface crítica, no se presenta como cerrado sin decirlo explícitamente

## 9. Preparar salida profesional

Al cerrar una tanda:

- dejar la rama limpia
- preparar commit o commits coherentes
- hacer push y abrir PR cuando el flujo normal no esté bloqueado
- entregar texto de PR cuando aporte claridad
- si hay impacto en otros repos, redactar issues bien formuladas y con `labels`

Regla:

- no dar por terminado un slice con diff real si todavía falta el paso rutinario de commit, push o PR y no hay bloqueo real

## 10. Cerrar y dejar base limpia

Al final:

- volver a `main` cuando proceda
- limpiar ramas mergeadas si toca
- no arrastrar archivos no relacionados
- dejar claro cuál es el siguiente bloque lógico

Esto incluye, cuando aplique:

- cerrar el issue vinculado después del merge
- eliminar la rama local mergeada
- eliminar la rama remota mergeada
- eliminar o limpiar el worktree asociado si se usó uno
- ejecutar `fetch --prune` para no seguir viendo ramas remotas ya cerradas
- evitar que queden commits o ramas “temporales” sin contexto claro en local o remoto

## 10.1 Postura local autoritativa

Después de merges y limpiezas, el repositorio debe conservar una base local inequívoca.

Postura correcta:

- el worktree principal debe ser el checkout canónico
- ese checkout canónico debe estar en `main`
- `main` local debe quedar alineado con `origin/main` antes de abrir el siguiente slice
- los nuevos slices deben arrancar desde ramas o worktrees dedicados creados desde `origin/main`

Cuándo conservar un worktree secundario:

- sigue ligado a una issue o PR activa
- todavía tiene trabajo local único o contexto intencional no mergeado
- no es solo una copia atrasada de historia ya absorbida por `main`

Cuándo cerrarlo:

- no tiene commits únicos frente a `origin/main`
- su upstream remoto desapareció y el trabajo ya está merged o superseded
- la issue o PR vinculada ya está cerrada
- ya no sirve como base válida para la siguiente sesión

Si un worktree está sucio pero sigue vivo, debe quedar identificado explícitamente como la excepción activa.

## Orden estratégico actual de `quant_lab`

A día de hoy, el orden correcto es:

1. cerrar y endurecer `Stage D.2 - supervised broker submit safety` sobre los corredores ya implementados
2. seguir puliendo `Stage C.1 - Paper Trading Operationalization` cuando fortalezca promoción, runbooks o visibilidad operativa
3. hardening puntual de frontera externa solo si hay fricción real
4. no reabrir `Stage D.0` o `Stage D.1` como bloques principales salvo que un fallo real demuestre un gap de boundary
5. pasar a `live supervisado` solo cuando el corredor actual tenga evidencia operativa creíble
6. dejar `automatización controlada` para después de esa credibilidad operativa

Interpretación:

- Stepbit no dicta el roadmap de QuantLab
- la frontera externa se mejora cuando ayuda, no cuando desplaza prioridades soberanas
- `paper` sigue siendo prerrequisito, pero ya no es el cuello principal del roadmap
- la prioridad actual es producir evidencia real y endurecer el punto exacto que falle en los corredores supervisados existentes

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
- no trabajar desde ramas con upstream `gone`
- no hacer push directo a `main`
