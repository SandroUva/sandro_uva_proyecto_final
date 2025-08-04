"""
Configuración de Base de Datos para Sistema ASADAS Tsa Diglo
Conexión SQLite para desarrollo, fácil migración a PostgreSQL
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from pathlib import Path
from typing import Generator

# Importar modelos
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import Base, DEFAULT_CONFIG, SystemConfiguration

# Configuración de base de datos
DATABASE_URL = "sqlite:///./asadas_tsa_diglo.db"

# Crear engine con configuración optimizada para SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,  # Permite múltiples threads
        "timeout": 20  # Timeout en segundos
    },
    poolclass=StaticPool,
    echo=False  # Cambiar a True para debug SQL
)


# Habilitar foreign keys en SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")  # Mejor concurrencia
    cursor.execute("PRAGMA synchronous=NORMAL")  # Balance rendimiento/seguridad
    cursor.close()


# SessionLocal para crear sesiones de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_database():
    """
    Dependency para obtener sesión de base de datos
    Usar con FastAPI dependency injection
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Obtener sesión de base de datos para uso directo
    """
    return SessionLocal()


def init_database():
    """
    Inicializar base de datos: crear tablas y configuración por defecto
    """
    print("🗄️ Inicializando base de datos...")

    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas exitosamente")

    # Insertar configuración por defecto
    setup_default_config()
    print("✅ Configuración por defecto cargada")

    print("🎉 Base de datos inicializada correctamente")


def setup_default_config():
    """
    Insertar configuración por defecto si no existe
    """
    db = SessionLocal()
    try:
        # Verificar si ya existe configuración
        existing_config = db.query(SystemConfiguration).first()
        if existing_config:
            print("ℹ️ Configuración ya existe, omitiendo...")
            return

        # Insertar configuración por defecto
        for key, value in DEFAULT_CONFIG.items():
            config_item = SystemConfiguration(
                config_key=key,
                config_value=value,
                description=f"Configuración por defecto para {key}"
            )
            db.add(config_item)

        db.commit()
        print(f"✅ {len(DEFAULT_CONFIG)} configuraciones agregadas")

    except Exception as e:
        print(f"❌ Error configurando base de datos: {e}")
        db.rollback()
    finally:
        db.close()


def get_config_value(key: str, default_value: str = None) -> str:
    """
    Obtener valor de configuración de la base de datos
    """
    db = SessionLocal()
    try:
        config = db.query(SystemConfiguration).filter(
            SystemConfiguration.config_key == key
        ).first()

        if config:
            return config.config_value
        return default_value
    finally:
        db.close()


def update_config_value(key: str, value: str, description: str = None):
    """
    Actualizar o crear valor de configuración
    """
    db = SessionLocal()
    try:
        config = db.query(SystemConfiguration).filter(
            SystemConfiguration.config_key == key
        ).first()

        if config:
            config.config_value = value
            if description:
                config.description = description
        else:
            config = SystemConfiguration(
                config_key=key,
                config_value=value,
                description=description or f"Configuración para {key}"
            )
            db.add(config)

        db.commit()
        return True
    except Exception as e:
        print(f"❌ Error actualizando configuración {key}: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def check_database_connection() -> bool:
    """
    Verificar conexión a la base de datos
    """
    try:
        db = SessionLocal()
        # Intenta hacer una consulta simple
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Error de conexión a base de datos: {e}")
        return False


def get_database_info():
    """
    Obtener información sobre la base de datos
    """
    try:
        db = SessionLocal()

        # Obtener información de las tablas
        tables_info = {}

        # Contar registros en cada tabla principal
        from database.models import TankReading, Alert, PumpOperation, ChlorineOperation

        tables_info['tank_readings'] = db.query(TankReading).count()
        tables_info['alerts'] = db.query(Alert).count()
        tables_info['pump_operations'] = db.query(PumpOperation).count()
        tables_info['chlorine_operations'] = db.query(ChlorineOperation).count()
        tables_info['system_config'] = db.query(SystemConfiguration).count()

        db.close()
        return tables_info
    except Exception as e:
        print(f"❌ Error obteniendo info de base de datos: {e}")
        return {}


def reset_database():
    """
    CUIDADO: Elimina y recrea toda la base de datos
    Solo usar en desarrollo
    """
    print("⚠️ ADVERTENCIA: Eliminando toda la base de datos...")

    # Eliminar todas las tablas
    Base.metadata.drop_all(bind=engine)
    print("🗑️ Tablas eliminadas")

    # Recrear base de datos
    init_database()
    print("✅ Base de datos recreada")


# Función para ser llamada al iniciar la aplicación
def startup_database():
    """
    Función para ejecutar al iniciar la aplicación
    """
    print("🚀 Iniciando configuración de base de datos...")

    # Verificar si el archivo de base de datos existe
    db_file = "asadas_tsa_diglo.db"
    if not os.path.exists(db_file):
        print("📁 Base de datos no existe, creando...")
        init_database()
    else:
        print("📁 Base de datos encontrada")
        # Verificar conexión
        if check_database_connection():
            print("✅ Conexión a base de datos exitosa")
        else:
            print("❌ Error de conexión, recreando base de datos...")
            init_database()


if __name__ == "__main__":
    # Script para ejecutar directamente y configurar BD
    print("🔧 Configurando base de datos directamente...")
    startup_database()

    # Mostrar información
    info = get_database_info()
    print("\n📊 Información de la base de datos:")
    for table, count in info.items():
        print(f"  - {table}: {count} registros")