# Troubleshooting adicional

- `ModuleNotFoundError: reflex`: agrega `reflex` a requirements/pyproject y reinstala.
- El workflow no corre: revisa rama en `branches: [ main ]`.
- App en subcarpeta: usa `app_directory` en el Action.
- Variables no llegan: define Secrets y evita imprimirlas en logs.
