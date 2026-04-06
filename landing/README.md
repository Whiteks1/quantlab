# QuantLab Landing

Landing estatica preparada para publicarse en GitHub Pages.

## Governance

- Source of truth: `../docs/brand-guidelines.md`
- Landing workflow: `../docs/landing-governance.md`
- Folder-specific rules: `./AGENTS.md`

If a copy, brand, or layout change touches the public position of QuantLab Research, update the canonical docs first and the landing surface second.

## Estructura

- `index.html`
- `styles.css`
- `app.js`

## Preview local

Se puede abrir `index.html` directamente o servir la carpeta `landing/` con cualquier servidor estatico.

## Deploy

El workflow [pages.yml](../.github/workflows/pages.yml) publica el contenido de `landing/` en GitHub Pages cuando hay cambios en `main`.

Requisito del repositorio:

- GitHub Pages debe estar configurado para desplegar desde **GitHub Actions**.
