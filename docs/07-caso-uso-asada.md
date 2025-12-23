# Caso de uso — ASADA Tsa Diglo: Monitoreo de Tanques

## 1) Contexto operativo
En la ASADA (acueducto rural) **Tsa Diglo** se gestionan **dos tanques**:
- **Tanque A — “cisterna”**: se alimenta de las captaciones; su función es **almacenar** y **activar una bomba** cuando está lleno para enviar agua al Tanque B.
- **Tanque B — “tanque 150”**: con **150 m³** de capacidad; **alimenta 10 tanques quiebragradientes** (descarga por gravedad).

## 2) Objetivos de monitoreo y control
- Medir continuamente **nivel de agua** y **nivel de cloro** del **Tanque B**.
- Con base en esos datos:
  - Mejorar la **programación del bombeo** (evitar sobrebombeo y faltantes).
  - **Encender/apagar** la **máquina de cloración** según umbrales definidos por operación.
- **Alertar por correo** ante condiciones fuera de rango.
- **Guardar lecturas** en una **BD** para:
  - **Gráficos históricos**.
  - **Modelos de IA** (proyecciones y detección de anomalías).

## 3) Alcance técnico
- **Frontend/Backend**: Python con **Reflex** (UI/UX moderna).
- **Control de versiones**: Git + GitHub.
- **Despliegue**: CI/CD (GitHub Actions) → Reflex Cloud.
- **Alertas**: correo electrónico (SMTP) basadas en umbrales configurables.
- **Simulación**: **API propia** que emula un Raspberry Pi/Arduino mientras no hay hardware real.
- **Persistencia**: Base de datos (inicialmente **SQLite** para desarrollo; **PostgreSQL** recomendado en producción).

## 4) Datos y base de datos
### Esquema mínimo propuesto
- **tanks**
  - `id` (PK)
  - `name` (str) — ej. "cisterna", "tanque_150"
  - `capacity_m3` (float, opcional)
- **sensors**
  - `id` (PK)
  - `tank_id` (FK → tanks.id)
  - `kind` (enum: `level`, `chlorine`)
  - `unit` (str, ej. `m`, `ppm`)
  - `label` (str) — identificador legible
- **readings**
  - `id` (PK)
  - `sensor_id` (FK → sensors.id)
  - `value` (float)
  - `ts` (timestamp, indexado)
- **thresholds** (umbrales de alerta por sensor o tanque)
  - `id` (PK)
  - `sensor_id` (FK) **o** `tank_id` (cuando aplica al conjunto)
  - `min_value` (float, opcional)
  - `max_value` (float, opcional)
  - `email_recipients` (str, CSV) — destinos por correo
- **alerts**
  - `id` (PK)
  - `reading_id` (FK → readings.id)
  - `level` (enum: `info`, `warning`, `critical`)
  - `message` (str)
  - `sent_at` (timestamp)

> Para desarrollo se puede iniciar con **SQLite** y migrar a **PostgreSQL** en producción.

### Variables de entorno sugeridas
```
ENV=dev
DATABASE_URL=sqlite:///./data.db        # o postgres://user:pass@host/db
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=usuario@example.com
SMTP_PASS=super-secreto
ALERT_FROM=alertas@asada.tsa
ALERT_TO=operacion@asada.tsa, soporte@asada.tsa
# Umbrales por defecto (opcional, JSON):
DEFAULT_THRESHOLDS={"chlorine_ppm":{"min":0.2,"max":1.5},"level_m":{"min":0.4,"max":4.5}}
```

## 5) API de simulación (para pruebas sin hardware)
- **POST** `/api/v1/readings/ingest`
  - Body (JSON):
    ```json
    { "sensor_label": "tanque150_chlorine", "value": 0.9, "ts": "2025-08-13T12:01:00Z" }
    ```
  - Acción: valida y almacena lectura; evalúa umbrales → dispara alertas si aplica.
- **GET** `/api/v1/readings/latest?tank=tanque_150`
  - Retorna última lectura por tipo de sensor (nivel, cloro) para ese tanque.
- **GET** `/api/v1/readings/history?tank=tanque_150&kind=chlorine&from=...&to=...`
  - Devuelve series históricas para gráficos.
- **GET** `/api/v1/thresholds`
  - Configuración de umbrales vigentes.
- **POST** `/api/v1/alerts/test`
  - Envía correo de prueba para validar SMTP.

> Internamente se puede implementar con **FastAPI** y SQLModel/SQLAlchemy.

## 6) Integración con Reflex (UI/UX)
- Página principal con **tarjetas** de estado (nivel y cloro) del Tanque B.
- **Gráficos históricos** (línea/área) por variable.
- **Indicadores** (semáforo) según rango.
- Panel de **configuración de umbrales** y **destinatarios de alertas**.
- **Toast/Modal** cuando se dispare una alerta reciente.
- Botón de **simular** lectura para pruebas.

## 7) Señales y control (bombeo y cloración)
- La lógica de control (encender/apagar) se gestiona por eventos en el backend (jobs programados o listeners al almacenar lecturas).
- Se deja listo para conectar a actuadores reales cuando haya hardware (GPIO/PLC/API).

## 8) IA y analítica
- Con los históricos, se podrán construir:
  - **Pronósticos** de nivel/cloro (p. ej. modelos ARIMA/prophet o regresión).
  - **Detección de anomalías** (z-score, isolation forest, etc.).
- La capa de IA será un módulo aparte para no bloquear el MVP.

## 9) Entregables
- **UI Reflex** funcional y desplegada.
- **API de simulación** con endpoints operativos.
- **BD** con migraciones básicas y consultas agregadas.
- **Alertas por correo** configurables.
- **Documentación** (esta página + README + .env.example).
