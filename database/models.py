"""
Modelos de Base de Datos para Sistema ASADAS Tsa Diglo
Sistema de Monitoreo de Tanques A (Cisterna) y B (150m³)
"""

from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class TankReading(Base):
    """
    Tabla principal para almacenar lecturas de sensores
    Tanque A (Cisterna) y Tanque B (150m³)
    """
    __tablename__ = "tank_readings"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=func.now(), index=True)

    # Identificación del tanque
    tank_id = Column(String(10), index=True)  # 'tank_a' o 'tank_b'
    tank_name = Column(String(50))  # 'Cisterna' o 'Tanque 150'

    # Mediciones de nivel de agua
    water_level_cm = Column(Float)  # Nivel en centímetros
    water_level_percent = Column(Float)  # Porcentaje de capacidad
    water_volume_m3 = Column(Float)  # Volumen en metros cúbicos

    # Mediciones de cloro (solo Tanque B)
    chlorine_ppm = Column(Float, nullable=True)  # Partes por millón
    chlorine_status = Column(String(20), nullable=True)  # 'normal', 'low', 'high'

    # Estado del sistema
    pump_status = Column(Boolean, default=False)  # Bomba encendida/apagada
    chlorinator_status = Column(Boolean, default=False)  # Clorador encendido/apagado

    # Metadatos
    sensor_status = Column(String(20), default='active')  # 'active', 'error', 'maintenance'
    data_source = Column(String(20), default='sensor')  # 'sensor', 'manual', 'simulation'


class Alert(Base):
    """
    Tabla para almacenar alertas del sistema
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=func.now(), index=True)

    # Información de la alerta
    alert_type = Column(String(30))  # 'water_level', 'chlorine', 'pump', 'sensor'
    severity = Column(String(10))  # 'low', 'medium', 'high', 'critical'
    tank_id = Column(String(10))  # 'tank_a', 'tank_b', 'system'

    # Mensaje y descripción
    title = Column(String(100))
    message = Column(Text)

    # Estado de la alerta
    status = Column(String(20), default='active')  # 'active', 'resolved', 'acknowledged'
    resolved_at = Column(DateTime, nullable=True)

    # Valores que activaron la alerta
    trigger_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)

    # Notificaciones
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime, nullable=True)


class SystemConfiguration(Base):
    """
    Tabla para configuraciones del sistema
    """
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(50), unique=True, index=True)
    config_value = Column(String(200))
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class PumpOperation(Base):
    """
    Tabla para registrar operaciones de bombeo
    """
    __tablename__ = "pump_operations"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime, nullable=True)

    # Información de la operación
    operation_type = Column(String(20))  # 'automatic', 'manual', 'scheduled'
    trigger_level_cm = Column(Float)  # Nivel que activó el bombeo
    target_level_cm = Column(Float)  # Nivel objetivo

    # Resultados
    volume_pumped_m3 = Column(Float, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    status = Column(String(20), default='active')  # 'active', 'completed', 'error'

    # Eficiencia
    energy_consumption_kwh = Column(Float, nullable=True)
    pump_efficiency_percent = Column(Float, nullable=True)


class ChlorineOperation(Base):
    """
    Tabla para registrar operaciones de cloración
    """
    __tablename__ = "chlorine_operations"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime, nullable=True)

    # Información de la operación
    operation_type = Column(String(20))  # 'automatic', 'manual', 'maintenance'
    initial_chlorine_ppm = Column(Float)
    target_chlorine_ppm = Column(Float)
    final_chlorine_ppm = Column(Float, nullable=True)

    # Dosificación
    chlorine_dose_ml = Column(Float, nullable=True)
    dosing_rate_ml_min = Column(Float, nullable=True)

    # Estado
    status = Column(String(20), default='active')  # 'active', 'completed', 'error'
    duration_minutes = Column(Integer, nullable=True)


class MaintenanceLog(Base):
    """
    Tabla para registrar mantenimientos y calibraciones
    """
    __tablename__ = "maintenance_log"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=func.now())

    # Información del mantenimiento
    maintenance_type = Column(String(30))  # 'calibration', 'cleaning', 'repair', 'inspection'
    equipment = Column(String(50))  # 'tank_a_sensor', 'tank_b_sensor', 'pump', 'chlorinator'

    # Detalles
    description = Column(Text)
    technician = Column(String(100))
    duration_hours = Column(Float, nullable=True)

    # Resultados
    status = Column(String(20))  # 'completed', 'pending', 'failed'
    notes = Column(Text, nullable=True)
    next_maintenance = Column(DateTime, nullable=True)


# Configuraciones por defecto del sistema
DEFAULT_CONFIG = {
    # Umbrales de Tanque A (Cisterna)
    'tank_a_min_level_cm': '20',  # Nivel mínimo antes de alerta
    'tank_a_max_level_cm': '180',  # Nivel máximo (activar bomba)
    'tank_a_capacity_m3': '50',  # Capacidad total

    # Umbrales de Tanque B (150m³)
    'tank_b_min_level_cm': '30',  # Nivel mínimo crítico
    'tank_b_max_level_cm': '300',  # Nivel máximo
    'tank_b_capacity_m3': '150',  # Capacidad total

    # Cloro
    'chlorine_min_ppm': '0.5',  # Cloro mínimo
    'chlorine_max_ppm': '2.0',  # Cloro máximo
    'chlorine_optimal_ppm': '1.2',  # Cloro óptimo

    # Bombeo
    'pump_cycle_min_minutes': '10',  # Tiempo mínimo entre ciclos
    'pump_max_runtime_hours': '4',  # Tiempo máximo continuo

    # Alertas
    'email_notifications': 'true',
    'email_recipients': 'admin@asadas-tsadiglo.cr',
    'alert_frequency_minutes': '15',  # Frecuencia de verificación

    # Sistema
    'data_retention_days': '365',  # Retención de datos
    'backup_frequency_hours': '24',  # Frecuencia de respaldo
}