"""
Generador de datos de sensores para el sistema ASADAS Tsa Diglo
Simula lecturas de tanques de agua con bomba y cloración
"""

import random
import time
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Any, Optional


class TankType(Enum):
    TANK_A = "tank_a"  # Cisterna
    TANK_B = "tank_b"  # Tanque 150m³


@dataclass
class TankConfig:
    tank_id: str
    name: str
    capacity_m3: float
    max_height_cm: float
    min_height_cm: float
    has_chlorine_sensor: bool
    normal_consumption_rate: float  # m³/hour


# Configuraciones de tanques
TANK_CONFIGS = {
    TankType.TANK_A: TankConfig(
        tank_id="tank_a",
        name="Cisterna",
        capacity_m3=50.0,
        max_height_cm=180.0,
        min_height_cm=10.0,
        has_chlorine_sensor=False,
        normal_consumption_rate=0.0  # No se consume, solo se llena
    ),
    TankType.TANK_B: TankConfig(
        tank_id="tank_b",
        name="Tanque 150",
        capacity_m3=150.0,
        max_height_cm=300.0,
        min_height_cm=20.0,
        has_chlorine_sensor=True,
        normal_consumption_rate=2.5  # m³/hour consumo promedio
    )
}


class SensorDataGenerator:
    def __init__(self):
        self.start_time = datetime.now()

        # Estados iniciales de los tanques
        self.tank_states = {
            TankType.TANK_A: {
                "water_level_cm": 120.0,  # Nivel inicial cisterna
                "pump_running": False,
                "last_pump_change": datetime.now(),
                "temperature": 24.0,
                "flow_rate": 0.0
            },
            TankType.TANK_B: {
                "water_level_cm": 200.0,  # Nivel inicial tanque 150
                "chlorine_ppm": 1.2,
                "chlorinator_running": False,
                "last_chlorinator_change": datetime.now(),
                "temperature": 23.0,
                "flow_rate": 0.0,
                "ph": 7.2
            }
        }

        # Patrones de consumo por hora del día
        self.consumption_patterns = {
            0: 0.5, 1: 0.3, 2: 0.2, 3: 0.2, 4: 0.3, 5: 0.8,
            6: 1.5, 7: 2.0, 8: 1.8, 9: 1.2, 10: 1.0, 11: 1.3,
            12: 1.8, 13: 1.5, 14: 1.2, 15: 1.0, 16: 1.2, 17: 1.8,
            18: 2.2, 19: 2.5, 20: 2.0, 21: 1.5, 22: 1.2, 23: 0.8
        }

    def update_tank_levels(self):
        """Actualizar niveles de agua según lógica del sistema"""
        current_hour = datetime.now().hour
        consumption_multiplier = self.consumption_patterns.get(current_hour, 1.0)

        # ============= TANQUE A (CISTERNA) =============
        tank_a_state = self.tank_states[TankType.TANK_A]
        config_a = TANK_CONFIGS[TankType.TANK_A]

        # Lógica automática de bomba si no está en modo manual
        current_level_a = tank_a_state["water_level_cm"]
        current_percent_a = (current_level_a / config_a.max_height_cm) * 100

        # La bomba se enciende automáticamente cuando la cisterna está llena (≥85%)
        # y se apaga cuando baja a ≤60%
        if not hasattr(self, 'pump_manual_override'):
            if current_percent_a >= 85 and not tank_a_state["pump_running"]:
                tank_a_state["pump_running"] = True
                tank_a_state["last_pump_change"] = datetime.now()
            elif current_percent_a <= 60 and tank_a_state["pump_running"]:
                tank_a_state["pump_running"] = False
                tank_a_state["last_pump_change"] = datetime.now()

        # Simular entrada de agua a la cisterna (captaciones)
        inflow_rate = random.uniform(3.0, 8.0)  # m³/hour entrada variable

        # Si la bomba está funcionando, bombear agua al tanque B
        outflow_rate = 12.0 if tank_a_state["pump_running"] else 0.0  # m³/hour bomba

        # Cambio neto en la cisterna
        net_change_m3 = (inflow_rate - outflow_rate) / 60  # Por minuto
        level_change_cm = (net_change_m3 / (config_a.capacity_m3 / config_a.max_height_cm))

        new_level_a = max(config_a.min_height_cm,
                         min(config_a.max_height_cm,
                             tank_a_state["water_level_cm"] + level_change_cm))

        tank_a_state["water_level_cm"] = new_level_a
        tank_a_state["flow_rate"] = outflow_rate if tank_a_state["pump_running"] else 0.0

        # ============= TANQUE B (TANQUE 150) =============
        tank_b_state = self.tank_states[TankType.TANK_B]
        config_b = TANK_CONFIGS[TankType.TANK_B]

        # Entrada desde la bomba del tanque A
        inflow_b = outflow_rate if tank_a_state["pump_running"] else 0.0

        # Consumo variable según hora del día
        consumption_rate = config_b.normal_consumption_rate * consumption_multiplier
        consumption_rate += random.uniform(-0.5, 0.5)  # Variación aleatoria

        # Cambio neto en tanque B
        net_change_b_m3 = (inflow_b - consumption_rate) / 60  # Por minuto
        level_change_b_cm = (net_change_b_m3 / (config_b.capacity_m3 / config_b.max_height_cm))

        new_level_b = max(config_b.min_height_cm,
                         min(config_b.max_height_cm,
                             tank_b_state["water_level_cm"] + level_change_b_cm))

        tank_b_state["water_level_cm"] = new_level_b
        tank_b_state["flow_rate"] = consumption_rate

        # ============= SISTEMA DE CLORACIÓN =============
        current_chlorine = tank_b_state["chlorine_ppm"]

        # Lógica automática del clorador
        if not hasattr(self, 'chlorinator_manual_override'):
            if current_chlorine < 0.8 and not tank_b_state["chlorinator_running"]:
                tank_b_state["chlorinator_running"] = True
                tank_b_state["last_chlorinator_change"] = datetime.now()
            elif current_chlorine > 1.5 and tank_b_state["chlorinator_running"]:
                tank_b_state["chlorinator_running"] = False
                tank_b_state["last_chlorinator_change"] = datetime.now()

        # Cambio en niveles de cloro
        if tank_b_state["chlorinator_running"]:
            chlorine_addition = 0.15  # ppm/hora cuando está activo
        else:
            chlorine_addition = 0.0

        # Degradación natural del cloro
        chlorine_degradation = 0.05  # ppm/hora degradación natural

        # Dilución por agua nueva
        dilution_factor = 1.0
        if inflow_b > 0:
            dilution_factor = 1 - (inflow_b / (config_b.capacity_m3 * (new_level_b / config_b.max_height_cm)))

        net_chlorine_change = ((chlorine_addition - chlorine_degradation) * dilution_factor) / 60
        new_chlorine = max(0.0, min(3.0, current_chlorine + net_chlorine_change))
        tank_b_state["chlorine_ppm"] = new_chlorine

    def get_tank_reading(self, tank_type: TankType) -> Dict[str, Any]:
        """Generar lectura completa de un tanque específico"""
        config = TANK_CONFIGS[tank_type]
        state = self.tank_states[tank_type]

        # Calcular métricas básicas
        current_level = state["water_level_cm"]
        level_percent = (current_level / config.max_height_cm) * 100
        volume_m3 = config.capacity_m3 * (current_level / config.max_height_cm)

        # Agregar ruido realista a las mediciones
        level_noise = random.uniform(-0.5, 0.5)
        temp_noise = random.uniform(-0.3, 0.3)

        reading = {
            "tank_id": config.tank_id,
            "tank_name": config.name,
            "timestamp": datetime.now(),
            "water_level_cm": round(current_level + level_noise, 2),
            "water_level_percent": round(level_percent, 1),
            "water_volume_m3": round(volume_m3, 2),
            "temperature": round(state["temperature"] + temp_noise, 1),
            "capacity_m3": config.capacity_m3,
            "max_height_cm": config.max_height_cm,
            "status": "normal"
        }

        # Datos específicos por tipo de tanque
        if tank_type == TankType.TANK_A:
            reading.update({
                "pump_status": state["pump_running"],
                "pump_last_change": state["last_pump_change"],
                "flow_rate_m3h": round(state["flow_rate"], 2),
                "inflow_estimated": round(random.uniform(3.0, 8.0), 2)
            })

        elif tank_type == TankType.TANK_B:
            chlorine_noise = random.uniform(-0.05, 0.05)
            reading.update({
                "chlorine_ppm": round(state["chlorine_ppm"] + chlorine_noise, 3),
                "chlorine_status": self._get_chlorine_status(state["chlorine_ppm"]),
                "chlorinator_status": state["chlorinator_running"],
                "chlorinator_last_change": state["last_chlorinator_change"],
                "consumption_rate_m3h": round(state["flow_rate"], 2),
                "ph": round(state["ph"] + random.uniform(-0.1, 0.1), 2)
            })

        # Estados de alerta
        if level_percent < 20:
            reading["status"] = "low_water"
        elif level_percent > 90:
            reading["status"] = "high_water"
        elif tank_type == TankType.TANK_B and state["chlorine_ppm"] < 0.5:
            reading["status"] = "low_chlorine"
        elif tank_type == TankType.TANK_B and state["chlorine_ppm"] > 2.0:
            reading["status"] = "high_chlorine"

        return reading

    def _get_chlorine_status(self, chlorine_ppm: float) -> str:
        """Determinar estado del cloro según niveles"""
        if chlorine_ppm < 0.5:
            return "low"
        elif chlorine_ppm > 2.0:
            return "high"
        elif 0.8 <= chlorine_ppm <= 1.5:
            return "optimal"
        else:
            return "normal"


# Instancia global del generador
sensor_generator = SensorDataGenerator()


def get_latest_readings() -> List[Dict[str, Any]]:
    """Obtener lecturas actuales de todos los tanques"""
    # Actualizar estados antes de generar lecturas
    sensor_generator.update_tank_levels()

    readings = []
    for tank_type in TankType:
        reading = sensor_generator.get_tank_reading(tank_type)
        readings.append(reading)

    return readings


def get_tank_reading(tank_id: str) -> Dict[str, Any]:
    """Obtener lectura de un tanque específico"""
    # Mapear tank_id a TankType
    tank_type = None
    if tank_id == "tank_a":
        tank_type = TankType.TANK_A
    elif tank_id == "tank_b":
        tank_type = TankType.TANK_B
    else:
        raise ValueError(f"tank_id inválido: {tank_id}")

    # Actualizar estados
    sensor_generator.update_tank_levels()

    return sensor_generator.get_tank_reading(tank_type)


# Función de prueba
if __name__ == "__main__":
    print("🧪 Probando generador de datos...")

    for i in range(5):
        print(f"\n--- Lectura {i+1} ---")
        readings = get_latest_readings()

        for reading in readings:
            print(f"{reading['tank_name']}: {reading['water_level_percent']:.1f}% "
                  f"({reading['water_level_cm']:.1f}cm)")

            if 'pump_status' in reading:
                print(f"  Bomba: {'🟢 ON' if reading['pump_status'] else '🔴 OFF'}")

            if 'chlorine_ppm' in reading:
                print(f"  Cloro: {reading['chlorine_ppm']:.3f} ppm "
                      f"({'🟢 ON' if reading['chlorinator_status'] else '🔴 OFF'})")

        time.sleep(2)