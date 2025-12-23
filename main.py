"""
API FastAPI para Sistema ASADAS Tsa Diglo
Endpoints para servir datos de sensores simulados con controles manuales
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
from datetime import datetime, timedelta
import asyncio
import os
import uvicorn
from contextlib import asynccontextmanager

# ✅ Import explícito (evita conflicto por archivos duplicados)
from simulation_api.data_generator import (
    sensor_generator,
    get_latest_readings,
    get_tank_reading,
    TankType,
    TANK_CONFIGS,
)

# =================== VARIABLES GLOBALES ===================

latest_readings_cache: List[Dict[str, Any]] = []
last_update: datetime = datetime.now()

manual_controls = {
    "pump_manual_mode": False,          # False = automático, True = manual
    "pump_manual_state": False,         # Estado manual de la bomba
    "chlorinator_manual_mode": False,   # False = automático, True = manual
    "chlorinator_manual_state": False,  # Estado manual del clorador
    "last_manual_action": {
        "pump": None,
        "chlorinator": None
    }
}

# ✅ Tu frontend real (fallback si no configurás FRONTEND_ORIGINS en cloud)
DEFAULT_FRONTEND_ORIGIN = "https://sandro-uva-proyecto-final-blue-sun.reflex.run"


# =================== UTILIDADES ===================

def iso(dt: Any) -> str:
    """Convierte datetime a ISO string para respuesta JSON segura."""
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


def apply_manual_controls() -> None:
    """Aplicar estados de control manual a los equipos (sobre el generador)"""
    # Control manual de bomba
    if manual_controls["pump_manual_mode"]:
        sensor_generator.tank_states[TankType.TANK_A]["pump_running"] = manual_controls["pump_manual_state"]

    # Control manual de clorador
    if manual_controls["chlorinator_manual_mode"]:
        sensor_generator.tank_states[TankType.TANK_B]["chlorinator_running"] = manual_controls["chlorinator_manual_state"]


async def update_readings_cache() -> None:
    """Actualizar cache de lecturas cada 30 segundos considerando controles manuales"""
    global latest_readings_cache, last_update

    while True:
        try:
            apply_manual_controls()
            latest_readings_cache = get_latest_readings()
            last_update = datetime.now()
            await asyncio.sleep(30)

        except Exception as e:
            # Importante: no matar el loop por un error puntual
            print(f"❌ Error actualizando cache: {e}")
            await asyncio.sleep(5)


# =================== LIFESPAN ===================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global latest_readings_cache, last_update

    # Inicializar cache
    latest_readings_cache = get_latest_readings()
    last_update = datetime.now()

    # Iniciar tarea en segundo plano
    task = asyncio.create_task(update_readings_cache())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


# =================== APP FASTAPI ===================

app = FastAPI(
    title="Asada Tsa Diglo Wak - API de Sensores y Control",
    description="API para monitoreo y control de tanques de agua y sistema de cloración",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# =================== CORS (cloud-safe) ===================
# Regla: si allow_credentials=True, NO se permite allow_origins=["*"].
# Usamos FRONTEND_ORIGINS si existe; si no, usamos tu Reflex URL + localhost.

origins_env = os.environ.get("FRONTEND_ORIGINS", "").strip()
allowed_origins = [o.strip().rstrip("/") for o in origins_env.split(",") if o.strip()]

if not allowed_origins:
    allowed_origins = [
        DEFAULT_FRONTEND_ORIGIN,        # ✅ tu frontend en Reflex Cloud
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =================== ENDPOINTS ===================

@app.get("/")
async def root():
    return {
        "message": "Asada Tsa Diglo Wak - Sistema de Monitoreo y Control de Tanques",
        "version": "2.0.0",
        "system": "Tanque A (Cisterna) + Tanque B (150m³)",
        "features": [
            "Monitoreo de nivel de agua en tiempo real",
            "Control automático y manual de bombeo",
            "Control automático y manual de cloración",
            "Sistema de alertas inteligente",
            "Datos históricos para análisis con IA",
        ],
        "control_endpoints": {
            "pump_on": "POST /api/control/pump/on",
            "pump_off": "POST /api/control/pump/off",
            "chlorinator_on": "POST /api/control/chlorinator/on",
            "chlorinator_off": "POST /api/control/chlorinator/off",
            "auto_mode": "POST /api/control/auto",
        },
        "monitoring_endpoints": {
            "current_readings": "GET /api/readings",
            "system_status": "GET /api/status",
            "control_status": "GET /api/control/status",
        },
        "timestamp": iso(datetime.now()),
        "status": "operational",
    }


@app.get("/api/readings")
async def get_current_readings():
    try:
        return {
            "success": True,
            "timestamp": iso(last_update),
            "readings": latest_readings_cache,
            "tanks_count": len(latest_readings_cache),
            "control_modes": {
                "pump_mode": "manual" if manual_controls["pump_manual_mode"] else "automatic",
                "chlorinator_mode": "manual" if manual_controls["chlorinator_manual_mode"] else "automatic",
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo lecturas: {str(e)}")


@app.get("/api/tank/{tank_id}")
async def get_tank_data(tank_id: str):
    if tank_id not in ["tank_a", "tank_b"]:
        raise HTTPException(status_code=400, detail="tank_id debe ser 'tank_a' o 'tank_b'")

    try:
        for reading in latest_readings_cache:
            if reading.get("tank_id") == tank_id:
                return {"success": True, "timestamp": iso(datetime.now()), "tank": reading}

        reading = get_tank_reading(tank_id)
        return {"success": True, "timestamp": iso(datetime.now()), "tank": reading}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo datos del tanque: {str(e)}")


@app.get("/api/status")
async def get_system_status():
    try:
        tank_a_data = None
        tank_b_data = None

        for reading in latest_readings_cache:
            if reading.get("tank_id") == "tank_a":
                tank_a_data = reading
            elif reading.get("tank_id") == "tank_b":
                tank_b_data = reading

        alerts = []

        if tank_a_data:
            level_percent = tank_a_data["water_level_percent"]
            if level_percent < 20:
                alerts.append({
                    "type": "low_water",
                    "tank": "tank_a",
                    "severity": "high",
                    "message": f"Nivel bajo en Cisterna: {level_percent}%",
                    "action_required": "Verificar captaciones de agua"
                })
            elif level_percent > 90:
                alerts.append({
                    "type": "high_water",
                    "tank": "tank_a",
                    "severity": "medium",
                    "message": f"Cisterna casi llena: {level_percent}%",
                    "action_required": "Bomba debería activarse automáticamente"
                })

        if tank_b_data:
            level_percent = tank_b_data["water_level_percent"]
            if level_percent < 25:
                alerts.append({
                    "type": "low_water",
                    "tank": "tank_b",
                    "severity": "critical",
                    "message": f"Nivel crítico en Tanque 150: {level_percent}%",
                    "action_required": "Activar bomba manualmente si es necesario"
                })

            chlorine = tank_b_data.get("chlorine_ppm")
            if chlorine is not None:
                if chlorine < 0.5:
                    alerts.append({
                        "type": "low_chlorine",
                        "tank": "tank_b",
                        "severity": "high",
                        "message": f"Cloro bajo: {chlorine} ppm",
                        "action_required": "Activar clorador manualmente"
                    })
                elif chlorine > 2.0:
                    alerts.append({
                        "type": "high_chlorine",
                        "tank": "tank_b",
                        "severity": "medium",
                        "message": f"Cloro alto: {chlorine} ppm",
                        "action_required": "Detener clorador temporalmente"
                    })

        return {
            "success": True,
            "timestamp": iso(datetime.now()),
            "system_operational": True,
            "tanks_online": len(latest_readings_cache),
            "last_reading": iso(last_update),
            "alerts": alerts,
            "alerts_count": len(alerts),
            "control_status": manual_controls,
            "tank_summary": {
                "tank_a": {
                    "name": "Cisterna",
                    "level_percent": tank_a_data["water_level_percent"] if tank_a_data else 0,
                    "level_cm": tank_a_data["water_level_cm"] if tank_a_data else 0,
                    "volume_m3": tank_a_data["water_volume_m3"] if tank_a_data else 0,
                    "pump_running": tank_a_data["pump_status"] if tank_a_data else False,
                    "pump_mode": "manual" if manual_controls["pump_manual_mode"] else "automatic",
                } if tank_a_data else None,
                "tank_b": {
                    "name": "Tanque 150",
                    "level_percent": tank_b_data["water_level_percent"] if tank_b_data else 0,
                    "level_cm": tank_b_data["water_level_cm"] if tank_b_data else 0,
                    "volume_m3": tank_b_data["water_volume_m3"] if tank_b_data else 0,
                    "chlorine_ppm": tank_b_data.get("chlorine_ppm", 0) if tank_b_data else 0,
                    "chlorine_status": tank_b_data.get("chlorine_status", "unknown") if tank_b_data else "unknown",
                    "chlorinator_running": tank_b_data.get("chlorinator_status", False) if tank_b_data else False,
                    "chlorinator_mode": "manual" if manual_controls["chlorinator_manual_mode"] else "automatic",
                } if tank_b_data else None,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado del sistema: {str(e)}")


# =================== CONTROLES MANUALES ===================

@app.post("/api/control/pump/on")
async def turn_pump_on():
    try:
        manual_controls["pump_manual_mode"] = True
        manual_controls["pump_manual_state"] = True
        manual_controls["last_manual_action"]["pump"] = {
            "action": "turn_on",
            "timestamp": iso(datetime.now()),
            "user": "manual_control",
        }
        sensor_generator.tank_states[TankType.TANK_A]["pump_running"] = True

        return {
            "success": True,
            "timestamp": iso(datetime.now()),
            "message": "🟢 BOMBA ENCENDIDA MANUALMENTE",
            "pump_status": "ON",
            "mode": "MANUAL",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error encendiendo bomba: {str(e)}")


@app.post("/api/control/pump/off")
async def turn_pump_off():
    try:
        manual_controls["pump_manual_mode"] = True
        manual_controls["pump_manual_state"] = False
        manual_controls["last_manual_action"]["pump"] = {
            "action": "turn_off",
            "timestamp": iso(datetime.now()),
            "user": "manual_control",
        }
        sensor_generator.tank_states[TankType.TANK_A]["pump_running"] = False

        return {
            "success": True,
            "timestamp": iso(datetime.now()),
            "message": "🔴 BOMBA APAGADA MANUALMENTE",
            "pump_status": "OFF",
            "mode": "MANUAL",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error apagando bomba: {str(e)}")


@app.post("/api/control/chlorinator/on")
async def turn_chlorinator_on():
    try:
        manual_controls["chlorinator_manual_mode"] = True
        manual_controls["chlorinator_manual_state"] = True
        manual_controls["last_manual_action"]["chlorinator"] = {
            "action": "turn_on",
            "timestamp": iso(datetime.now()),
            "user": "manual_control",
        }
        sensor_generator.tank_states[TankType.TANK_B]["chlorinator_running"] = True

        return {
            "success": True,
            "timestamp": iso(datetime.now()),
            "message": "🟢 CLORADOR ENCENDIDO MANUALMENTE",
            "chlorinator_status": "ON",
            "mode": "MANUAL",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error encendiendo clorador: {str(e)}")


@app.post("/api/control/chlorinator/off")
async def turn_chlorinator_off():
    try:
        manual_controls["chlorinator_manual_mode"] = True
        manual_controls["chlorinator_manual_state"] = False
        manual_controls["last_manual_action"]["chlorinator"] = {
            "action": "turn_off",
            "timestamp": iso(datetime.now()),
            "user": "manual_control",
        }
        sensor_generator.tank_states[TankType.TANK_B]["chlorinator_running"] = False

        return {
            "success": True,
            "timestamp": iso(datetime.now()),
            "message": "🔴 CLORADOR APAGADO MANUALMENTE",
            "chlorinator_status": "OFF",
            "mode": "MANUAL",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error apagando clorador: {str(e)}")


@app.post("/api/control/auto")
async def set_automatic_mode():
    try:
        manual_controls["pump_manual_mode"] = False
        manual_controls["chlorinator_manual_mode"] = False
        manual_controls["last_manual_action"]["pump"] = {
            "action": "set_automatic",
            "timestamp": iso(datetime.now()),
            "user": "manual_control",
        }
        manual_controls["last_manual_action"]["chlorinator"] = {
            "action": "set_automatic",
            "timestamp": iso(datetime.now()),
            "user": "manual_control",
        }

        return {
            "success": True,
            "timestamp": iso(datetime.now()),
            "message": "🤖 MODO AUTOMÁTICO ACTIVADO",
            "pump_mode": "AUTOMATIC",
            "chlorinator_mode": "AUTOMATIC",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error activando modo automático: {str(e)}")


@app.get("/api/control/status")
async def get_control_status():
    try:
        return {
            "success": True,
            "timestamp": iso(datetime.now()),
            "manual_controls": manual_controls,
            "current_states": {
                "pump_running": sensor_generator.tank_states[TankType.TANK_A]["pump_running"],
                "chlorinator_running": sensor_generator.tank_states[TankType.TANK_B]["chlorinator_running"],
            },
            "modes": {
                "pump": "MANUAL" if manual_controls["pump_manual_mode"] else "AUTOMATIC",
                "chlorinator": "MANUAL" if manual_controls["chlorinator_manual_mode"] else "AUTOMATIC",
            },
            "last_actions": manual_controls["last_manual_action"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado de controles: {str(e)}")


# =================== ENDPOINTS ADICIONALES ===================

@app.get("/api/history")
async def get_historical_data(hours: int = 24):
    if hours > 168:
        hours = 168

    try:
        historical_data = []
        now = datetime.now()
        points = hours * 2

        for i in range(points):
            timestamp = now - timedelta(minutes=30 * i)
            base_level_a = 120 + 10 * (i % 10) / 10
            base_level_b = 200 + 15 * (i % 8) / 8
            base_chlorine = 1.2 + 0.3 * (i % 6) / 6

            historical_data.append({
                "timestamp": iso(timestamp),
                "tank_a_level_cm": round(base_level_a, 2),
                "tank_a_level_percent": round((base_level_a / 180) * 100, 1),
                "tank_b_level_cm": round(base_level_b, 2),
                "tank_b_level_percent": round((base_level_b / 300) * 100, 1),
                "chlorine_ppm": round(base_chlorine, 3),
            })

        return {
            "success": True,
            "timestamp": iso(datetime.now()),
            "hours_requested": hours,
            "data_points": len(historical_data),
            "data": historical_data,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo datos históricos: {str(e)}")


@app.get("/api/config")
async def get_tank_configurations():
    try:
        configs = {}
        for tank_type, config in TANK_CONFIGS.items():
            configs[tank_type.value] = {
                "tank_id": config.tank_id,
                "name": config.name,
                "capacity_m3": config.capacity_m3,
                "max_height_cm": config.max_height_cm,
                "min_height_cm": config.min_height_cm,
                "has_chlorine_sensor": config.has_chlorine_sensor,
                "normal_consumption_rate": config.normal_consumption_rate,
            }

        return {
            "success": True,
            "timestamp": iso(datetime.now()),
            "configurations": configs,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo configuraciones: {str(e)}")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": iso(datetime.now()),
        "api_version": "2.0.0",
        "cache_updated": iso(last_update),
        "readings_cached": len(latest_readings_cache),
        "manual_controls_active": manual_controls["pump_manual_mode"] or manual_controls["chlorinator_manual_mode"],
    }


# =================== ENTRYPOINT LOCAL ===================

def run_server():
    """Ejecutar servidor (local o cloud si lo usan como entrypoint)"""
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # ✅ en cloud NO
        log_level="info",
    )


if __name__ == "__main__":
    print("🚀 Iniciando API Asada Tsa Diglo Wak v2.0...")
    print("📡 Servidor corriendo en: http://localhost:8000")
    print("📖 Documentación en: http://localhost:8000/docs")
    run_server()
