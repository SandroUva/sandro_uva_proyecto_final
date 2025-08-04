"""
Simulador de Datos de Sensores para Sistema ASADAS Tsa Diglo
Simula sensores de Arduino/Raspberry Pi para:
- Tanque A (Cisterna): Nivel de agua
- Tanque B (150m³): Nivel de agua + Cloro
"""

import random
import time
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class TankType(Enum):
    TANK_A = "tank_a"  # Cisterna
    TANK_B = "tank_b"  # Tanque 150m³


class SensorStatus(Enum):
    ACTIVE = "active"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class TankConfig:
    """Configuración de cada tanque"""
    tank_id: str
    name: str
    capacity_m3: float
    max_height_cm: float
    min_height_cm: float
    has_chlorine_sensor: bool
    normal_consumption_rate: float  # m³/hour


# Configuraciones de los tanques
TANK_CONFIGS = {
    TankType.TANK_A: TankConfig(
        tank_id="tank_a",
        name="Cisterna",
        capacity_m3=50.0,
        max_height_cm=180.0,
        min_height_cm=20.0,
        has_chlorine_sensor=False,
        normal_consumption_rate=2.5  # m³/hour
    ),
    TankType.TANK_B: TankConfig(
        tank_id="tank_b",
        name="Tanque 150",
        capacity_m3=150.0,
        max_height_cm=300.0,
        min_height_cm=30.0,
        has_chlorine_sensor=True,
        normal_consumption_rate=8.0  # m³/hour (alimenta 10 quiebragradientes)
    )
}


class SensorDataGenerator:
    """
    Generador de datos realistas para sensores de tanques
    """

    def __init__(self):
        self.tank_states = {
            TankType.TANK_A: {
                "current_level_cm": 120.0,  # Nivel inicial
                "pump_running": False,
                "last_pump_cycle": datetime.now() - timedelta(hours=2),
                "fill_rate": 0.0  # cm/min cuando se está llenando
            },
            TankType.TANK_B: {
                "current_level_cm": 200.0,  # Nivel inicial
                "chlorine_ppm": 1.2,
                "chlorinator_running": False,
                "last_chlorine_dose": datetime.now() - timedelta(hours=1),
                "consumption_rate": 0.0  # cm/min de consumo
            }
        }

        # Patrones de consumo por hora del día (0-23)
        self.consumption_patterns = {
            # Patrón típico de consumo de agua en comunidad rural
            0: 0.1, 1: 0.1, 2: 0.1, 3: 0.1, 4: 0.2,  # Madrugada - bajo
            5: 0.5, 6: 0.8, 7: 1.0, 8: 0.9, 9: 0.7,  # Mañana - medio-alto
            10: 0.6, 11: 0.8, 12: 1.0, 13: 0.9,  # Mediodía - alto
            14: 0.7, 15: 0.6, 16: 0.7, 17: 0.9,  # Tarde - medio-alto
            18: 1.0, 19: 0.9, 20: 0.8, 21: 0.6,  # Noche - alto inicial
            22: 0.4, 23: 0.2  # Noche tardía - bajo
        }

    def _calculate_level_from_volume(self, volume_m3: float, tank_type: TankType) -> float:
        """Calcular nivel en cm basado en volumen"""
        config = TANK_CONFIGS[tank_type]
        # Asumiendo tanque cilíndrico: nivel = volumen / área_base
        area_base_m2 = config.capacity_m3 / (config.max_height_cm / 100)
        level_m = volume_m3 / area_base_m2
        return level_m * 100  # convertir a cm

    def _calculate_volume_from_level(self, level_cm: float, tank_type: TankType) -> float:
        """Calcular volumen en m³ basado en nivel"""
        config = TANK_CONFIGS[tank_type]
        area_base_m2 = config.capacity_m3 / (config.max_height_cm / 100)
        level_m = level_cm / 100
        return level_m * area_base_m2

    def _get_consumption_multiplier(self) -> float:
        """Obtener multiplicador de consumo basado en hora del día"""
        current_hour = datetime.now().hour
        base_multiplier = self.consumption_patterns.get(current_hour, 0.5)

        # Añadir variación aleatoria ±20%
        variation = random.uniform(0.8, 1.2)
        return base_multiplier * variation

    def _simulate_tank_a_level(self, time_delta_minutes: float) -> float:
        """
        Simular nivel del Tanque A (Cisterna)
        - Se llena de captaciones (proceso continuo lento)
        - Se vacía cuando la bomba envía agua al Tanque B
        """
        state = self.tank_states[TankType.TANK_A]
        config = TANK_CONFIGS[TankType.TANK_A]

        current_level = state["current_level_cm"]

        # Llenado continuo de captaciones (2-5 cm/hora dependiendo de lluvia/época)
        season_factor = 1.0 + 0.3 * math.sin(time.time() / (24 * 3600))  # Variación diaria
        fill_rate_cm_hour = random.uniform(2.0, 5.0) * season_factor
        level_increase = (fill_rate_cm_hour / 60) * time_delta_minutes

        # Bomba se activa cuando nivel es alto, se desactiva cuando baja
        pump_should_run = current_level >= (config.max_height_cm * 0.85)  # 85% de capacidad
        pump_should_stop = current_level <= (config.max_height_cm * 0.60)  # 60% de capacidad

        if pump_should_run and not state["pump_running"]:
            state["pump_running"] = True
            state["last_pump_cycle"] = datetime.now()
        elif pump_should_stop and state["pump_running"]:
            state["pump_running"] = False

        # Si la bomba está corriendo, el nivel baja
        if state["pump_running"]:
            # Bomba envía ~15-20 m³/hour = ~6-8 cm/hour de reducción de nivel
            pump_rate_cm_hour = random.uniform(6.0, 8.0)
            level_decrease = (pump_rate_cm_hour / 60) * time_delta_minutes
            current_level -= level_decrease

        # Aplicar el llenado
        current_level += level_increase

        # Límites físicos
        current_level = max(config.min_height_cm, min(config.max_height_cm, current_level))

        # Añadir ruido del sensor (±2cm)
        sensor_noise = random.uniform(-2.0, 2.0)
        measured_level = current_level + sensor_noise

        # Actualizar estado
        state["current_level_cm"] = current_level

        return max(0, measured_level)

    def _simulate_tank_b_level(self, time_delta_minutes: float) -> float:
        """
        Simular nivel del Tanque B (150m³)
        - Se llena cuando la bomba del Tanque A está activa
        - Se vacía por consumo de los 10 quiebragradientes
        """
        state_a = self.tank_states[TankType.TANK_A]
        state_b = self.tank_states[TankType.TANK_B]
        config = TANK_CONFIGS[TankType.TANK_B]

        current_level = state_b["current_level_cm"]

        # Llenado desde Tanque A (cuando bomba A está activa)
        if state_a["pump_running"]:
            # La bomba envía agua del tanque A al B
            fill_rate_cm_hour = random.uniform(4.0, 6.0)  # cm/hour de incremento
            level_increase = (fill_rate_cm_hour / 60) * time_delta_minutes
            current_level += level_increase

        # Consumo por los quiebragradientes
        consumption_multiplier = self._get_consumption_multiplier()
        base_consumption_cm_hour = 3.0  # cm/hour base
        actual_consumption = base_consumption_cm_hour * consumption_multiplier
        level_decrease = (actual_consumption / 60) * time_delta_minutes
        current_level -= level_decrease

        # Límites físicos
        current_level = max(config.min_height_cm, min(config.max_height_cm, current_level))

        # Añadir ruido del sensor (±3cm)
        sensor_noise = random.uniform(-3.0, 3.0)
        measured_level = current_level + sensor_noise

        # Actualizar estado
        state_b["current_level_cm"] = current_level

        return max(0, measured_level)

    def _simulate_chlorine_level(self, time_delta_minutes: float) -> float:
        """
        Simular nivel de cloro en Tanque B
        - Decae naturalmente con el tiempo
        - Se incrementa cuando el clorador está activo
        """
        state = self.tank_states[TankType.TANK_B]
        current_chlorine = state["chlorine_ppm"]

        # Decaimiento natural del cloro (0.05-0.1 ppm/hora)
        decay_rate_ppm_hour = random.uniform(0.05, 0.1)
        chlorine_decrease = (decay_rate_ppm_hour / 60) * time_delta_minutes
        current_chlorine -= chlorine_decrease

        # Clorador se activa cuando nivel está bajo
        should_dose = current_chlorine < 0.8  # ppm mínimo para activar
        should_stop = current_chlorine > 1.5  # ppm máximo para desactivar

        if should_dose and not state["chlorinator_running"]:
            state["chlorinator_running"] = True
            state["last_chlorine_dose"] = datetime.now()
        elif should_stop and state["chlorinator_running"]:
            state["chlorinator_running"] = False

        # Si el clorador está activo, incrementar cloro
        if state["chlorinator_running"]:
            dose_rate_ppm_hour = random.uniform(0.3, 0.5)  # ppm/hora de incremento
            chlorine_increase = (dose_rate_ppm_hour / 60) * time_delta_minutes
            current_chlorine += chlorine_increase

        # Límites del cloro
        current_chlorine = max(0.0, min(3.0, current_chlorine))

        # Añadir ruido del sensor (±0.05 ppm)
        sensor_noise = random.uniform(-0.05, 0.05)
        measured_chlorine = current_chlorine + sensor_noise

        # Actualizar estado
        state["chlorine_ppm"] = current_chlorine

        return max(0.0, measured_chlorine)

    def generate_tank_reading(self, tank_type: TankType, time_delta_minutes: float = 1.0) -> Dict[str, Any]:
        """
        Generar lectura completa de un tanque
        """
        config = TANK_CONFIGS[tank_type]

        # Simular niveles
        if tank_type == TankType.TANK_A:
            level_cm = self._simulate_tank_a_level(time_delta_minutes)
        else:
            level_cm = self._simulate_tank_b_level(time_delta_minutes)

        # Calcular métricas derivadas
        volume_m3 = self._calculate_volume_from_level(level_cm, tank_type)
        level_percent = (level_cm / config.max_height_cm) * 100

        # Datos base
        reading = {
            "timestamp": datetime.now(),
            "tank_id": config.tank_id,
            "tank_name": config.name,
            "water_level_cm": round(level_cm, 2),
            "water_level_percent": round(level_percent, 1),
            "water_volume_m3": round(volume_m3, 2),
            "pump_status": self.tank_states[tank_type].get("pump_running", False),
            "sensor_status": SensorStatus.ACTIVE.value,
            "data_source": "simulation"
        }

        # Añadir datos de cloro si es Tanque B
        if tank_type == TankType.TANK_B and config.has_chlorine_sensor:
            chlorine_ppm = self._simulate_chlorine_level(time_delta_minutes)
            reading.update({
                "chlorine_ppm": round(chlorine_ppm, 3),
                "chlorine_status": self._get_chlorine_status(chlorine_ppm),
                "chlorinator_status": self.tank_states[tank_type]["chlorinator_running"]
            })

        return reading

    def _get_chlorine_status(self, chlorine_ppm: float) -> str:
        """Determinar estado del cloro"""
        if chlorine_ppm < 0.5:
            return "low"
        elif chlorine_ppm > 2.0:
            return "high"
        else:
            return "normal"

    def generate_all_readings(self, time_delta_minutes: float = 1.0) -> List[Dict[str, Any]]:
        """
        Generar lecturas de todos los tanques
        """
        readings = []
        for tank_type in TankType:
            reading = self.generate_tank_reading(tank_type, time_delta_minutes)
            readings.append(reading)
        return readings

    def simulate_sensor_error(self, tank_type: TankType, error_probability: float = 0.05) -> Dict[str, Any]:
        """
        Simular errores de sensores ocasionales
        """
        if random.random() < error_probability:
            config = TANK_CONFIGS[tank_type]
            return {
                "timestamp": datetime.now(),
                "tank_id": config.tank_id,
                "tank_name": config.name,
                "water_level_cm": None,
                "water_level_percent": None,
                "water_volume_m3": None,
                "chlorine_ppm": None if config.has_chlorine_sensor else None,
                "chlorine_status": "error" if config.has_chlorine_sensor else None,
                "pump_status": False,
                "chlorinator_status": False if config.has_chlorine_sensor else None,
                "sensor_status": SensorStatus.ERROR.value,
                "data_source": "simulation"
            }
        else:
            return self.generate_tank_reading(tank_type)

    def get_system_status(self) -> Dict[str, Any]:
        """
        Obtener estado general del sistema
        """
        return {
            "timestamp": datetime.now(),
            "tank_a_state": self.tank_states[TankType.TANK_A].copy(),
            "tank_b_state": self.tank_states[TankType.TANK_B].copy(),
            "system_operational": True,
            "last_reading": datetime.now()
        }


# Instancia global del generador
sensor_generator = SensorDataGenerator()


def get_latest_readings() -> List[Dict[str, Any]]:
    """Función principal para obtener lecturas actuales"""
    return sensor_generator.generate_all_readings()


def get_tank_reading(tank_id: str) -> Dict[str, Any]:
    """Obtener lectura de un tanque específico"""
    tank_type = TankType.TANK_A if tank_id == "tank_a" else TankType.TANK_B
    return sensor_generator.generate_tank_reading(tank_type)


if __name__ == "__main__":
    # Prueba del generador
    print("🧪 Probando simulador de sensores ASADAS Tsa Diglo...")

    generator = SensorDataGenerator()

    # Generar algunas lecturas de prueba
    for i in range(5):
        print(f"\n--- Lectura {i + 1} ---")
        readings = generator.generate_all_readings(1.0)

        for reading in readings:
            tank_name = reading["tank_name"]
            level = reading["water_level_cm"]
            percent = reading["water_level_percent"]
            volume = reading["water_volume_m3"]

            print(f"{tank_name}: {level}cm ({percent}%) = {volume}m³")

            if "chlorine_ppm" in reading:
                chlorine = reading["chlorine_ppm"]
                status = reading["chlorine_status"]
                print(f"  Cloro: {chlorine} ppm ({status})")

        time.sleep(2)  # Simular 2 minutos entre lecturas