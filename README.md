# sandro_uva_proyecto_final

Sistema web construido con **Reflex (Python full‑stack)**.  
Este repositorio corresponde al proyecto `sandro_uva_proyecto_final` y está preparado para desarrollo local y despliegue automático en **Reflex Cloud** desde GitHub.

- Repo: https://github.com/SandroUva/sandro_uva_proyecto_final
- Rama principal: `main`
- Lenguaje: Python 3.11+

## 📁 Estructura (actual en el repo)
```
assets/          # Estáticos
components/      # Componentes reutilizables de UI
database/        # Conexión / modelos / persistencia (si aplica)
pages/           # Páginas Reflex (rutas)
sandro_uva_proyecto_final/  # Paquete base (helpers/estados)
scripts/         # Scripts utilitarios
simulation_api/  # API de simulación de datos (para pruebas)
static/          # Archivos estáticos adicionales
tests/           # Pruebas
utils/           # Utilidades comunes
main.py          # Punto de entrada (si se ejecuta como app)
rxconfig.py      # Configuración de Reflex (app_name, etc.)
requirements.txt # Dependencias
```

> *Nota:* La estructura se infiere del listado del repositorio. Si cambias carpetas, actualizá esta sección.

## 🚀 Desarrollo local
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

pip install -r requirements.txt
# Iniciar en modo desarrollo
reflex run
# Producción local (build + serve optimizado)
reflex run --env prod
```

## 🔐 Variables de entorno
Crea un archivo `.env` (usa `./.env.example` como referencia). Variables típicas:
```
ENV=dev
LOG_LEVEL=INFO
# Agrega aquí claves necesarias de APIs/DB si aplica
# OPENAI_API_KEY=
# DATABASE_URL=
```

## ☁️ Despliegue automático a Reflex Cloud (CI/CD)
1. En **Reflex Cloud**, crea el proyecto y obtén:
   - **Project ID**
   - **Auth Token**
2. En el repo de GitHub: **Settings → Secrets and variables → Actions**:
   - `REFLEX_PROJECT_ID`
   - `REFLEX_AUTH_TOKEN`
3. Workflow en `.github/workflows/deploy.yml` (incluido en esta carpeta `docs_pack/`):
   - Despliega en cada `git push` a `main`.

### Workflow sugerido
```yaml
name: Deploy Reflex App

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Reflex Cloud
        uses: reflex-dev/reflex-deploy-action@v2
        with:
          auth_token: ${{ secrets.REFLEX_AUTH_TOKEN }}
          project_id: ${{ secrets.REFLEX_PROJECT_ID }}
          python_version: "3.12"
          # app_directory: "."  # si tu app vive en subcarpeta, cámbiala
          # extra_args: "--env OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}"
```

## 🧪 Pruebas
```bash
pytest -q
```

## 🛠️ Troubleshooting WebSocket (muy común al desplegar)
- **Síntoma:** consola muestra `Cannot connect to server: websocket error` y la URL apunta a otro host (p. ej. `*.fly.dev`).  
- **Solución rápida:** No fijar `api_url` en producción, dejar que Reflex determine el host.
  ```python
  # rxconfig.py (ejemplo seguro)
  import os, reflex as rx

  config = rx.Config(app_name="sandro_uva_proyecto_final")

  if os.getenv("ENV", "dev").lower() == "dev":
      # Solo en desarrollo local
      config.api_url = "http://localhost:8000"
  # En producción (Reflex Cloud) NO fijes api_url
  ```
- Asegúrate de usar `wss://` cuando sirves vía `https://` (Reflex Cloud lo maneja solo).
- En proxies/Nginx, habilita upgrade de WS (`Upgrade`/`Connection`).

## 🤝 Contribución
Lee `CONTRIBUTING.md` y las plantillas en `.github/`. Usa issues/PR con descripciones claras.

## 📝 Licencia
MIT © 2025 SandroUva



## Caso de uso: ASADA Tsa Diglo (Monitoreo de tanques)

En la ASADA (acueducto rural) **Tsa Diglo** se gestionan **dos tanques**:
- **Tanque A — “cisterna”**: recibe el agua de las captaciones y **almacena**. Cuando se llena, **activa la bomba** que envía agua al Tanque B.
- **Tanque B — “tanque 150”**: capacidad **150 m³**, alimenta **10 tanques quiebragradientes**.

**Objetivo del sistema**  
Monitorear en tiempo real el **nivel de agua** y el **nivel de cloro** del **Tanque B** para:
- Optimizar la **programación del bombeo** (encender/apagar la bomba desde la lógica de control).
- Encender/apagar la **máquina de cloración** según umbrales.
- **Alertar por correo** cuando los niveles salgan de rangos predefinidos.
- **Persistir datos** en una **base de datos** para gráficos históricos y **proyecciones con IA**.

> Implementación con **Python + Reflex**, versionado en **Git/GitHub** y **despliegue** (CI/CD) para visualización pública.
> Para pruebas, se usa una **API de simulación** que emula lecturas de un **Raspberry Pi/Arduino**.

➡️ Ver detalle en: `docs/07-caso-uso-asada.md`
