# Deploy a Reflex Cloud — Paso a paso

1) Crea proyecto en Reflex Cloud → copia Project ID y crea Auth Token.
2) Agrega `REFLEX_PROJECT_ID` y `REFLEX_AUTH_TOKEN` en GitHub Secrets.
3) Crea `.github/workflows/deploy.yml` (usa el que viene en este pack).
4) `git push` a `main`. Observa Actions y luego la URL en Reflex Cloud.
