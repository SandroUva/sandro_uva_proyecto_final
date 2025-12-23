"""
Cliente API para conectar Reflex con FastAPI
Maneja todas las comunicaciones con el servidor de sensores
"""

import httpx
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class SensorAPIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = 10.0

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Realizar petición HTTP async con manejo de errores"""
        url = f"{self.base_url}{endpoint}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, **kwargs)
                elif method.upper() == "POST":
                    response = await client.post(url, **kwargs)
                else:
                    raise ValueError(f"Método HTTP no soportado: {method}")

                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "timeout",
                "message": "Timeout conectando con API de sensores"
            }
        except httpx.ConnectError:
            return {
                "success": False,
                "error": "connection_error",
                "message": "No se puede conectar con API de sensores. ¿Está ejecutándose?"
            }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": "http_error",
                "message": f"Error HTTP {e.response.status_code}: {e.response.text}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": "unknown_error",
                "message": f"Error inesperado: {str(e)}"
            }

    def _make_sync_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Versión sincrónica para usar desde Reflex"""
        try:
            return asyncio.run(self._make_request(method, endpoint, **kwargs))
        except Exception as e:
            return {
                "success": False,
                "error": "sync_error",
                "message": f"Error en petición sincrónica: {str(e)}"
            }

    # =================== ENDPOINTS DE MONITOREO ===================

    def get_current_readings(self) -> Dict[str, Any]:
        """Obtener lecturas actuales de todos los sensores"""
        return self._make_sync_request("GET", "/api/readings")

    def get_tank_data(self, tank_id: str) -> Dict[str, Any]:
        """Obtener datos de un tanque específico"""
        return self._make_sync_request("GET", f"/api/tank/{tank_id}")

    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado del sistema con alertas"""
        return self._make_sync_request("GET", "/api/status")

    def get_historical_data(self, hours: int = 24) -> Dict[str, Any]:
        """Obtener datos históricos para gráficos"""
        return self._make_sync_request("GET", f"/api/history?hours={hours}")

    def get_tank_configurations(self) -> Dict[str, Any]:
        """Obtener configuraciones de tanques"""
        return self._make_sync_request("GET", "/api/config")

    # =================== ENDPOINTS DE CONTROL ===================

    def turn_pump_on(self) -> Dict[str, Any]:
        """🟢 Encender bomba manualmente"""
        return self._make_sync_request("POST", "/api/control/pump/on")

    def turn_pump_off(self) -> Dict[str, Any]:
        """🔴 Apagar bomba manualmente"""
        return self._make_sync_request("POST", "/api/control/pump/off")

    def turn_chlorinator_on(self) -> Dict[str, Any]:
        """🟢 Encender clorador manualmente"""
        return self._make_sync_request("POST", "/api/control/chlorinator/on")

    def turn_chlorinator_off(self) -> Dict[str, Any]:
        """🔴 Apagar clorador manualmente"""
        return self._make_sync_request("POST", "/api/control/chlorinator/off")

    def set_automatic_mode(self) -> Dict[str, Any]:
        """🤖 Activar modo automático completo"""
        return self._make_sync_request("POST", "/api/control/auto")

    def get_control_status(self) -> Dict[str, Any]:
        """Obtener estado de los controles manuales"""
        return self._make_sync_request("GET", "/api/control/status")

    # =================== UTILIDADES ===================

    def health_check(self) -> Dict[str, Any]:
        """Verificar si la API está funcionando"""
        return self._make_sync_request("GET", "/health")

    def is_api_available(self) -> bool:
        """Verificar rápidamente si la API está disponible"""
        result = self.health_check()
        return result.get("success", False) or "healthy" in str(result.get("status", ""))

    def get_api_info(self) -> Dict[str, Any]:
        """Obtener información general de la API"""
        return self._make_sync_request("GET", "/")


# Instancia global del cliente
api_client = SensorAPIClient()


# =================== FUNCIONES DE CONVENIENCIA ===================

def cargar_datos_sensores() -> Dict[str, Any]:
    """Función principal para cargar datos desde Reflex"""
    return api_client.get_current_readings()


def obtener_estado_sistema() -> Dict[str, Any]:
    """Obtener estado completo del sistema"""
    return api_client.get_system_status()


def obtener_datos_historicos(horas: int = 24) -> Dict[str, Any]:
    """Obtener datos para gráficos"""
    return api_client.get_historical_data(horas)


def controlar_bomba(accion: str) -> Dict[str, Any]:
    """Controlar bomba: 'on', 'off', 'auto'"""
    if accion.lower() == "on":
        return api_client.turn_pump_on()
    elif accion.lower() == "off":
        return api_client.turn_pump_off()
    elif accion.lower() == "auto":
        return api_client.set_automatic_mode()
    else:
        return {"success": False, "error": "invalid_action", "message": f"Acción inválida: {accion}"}


def controlar_clorador(accion: str) -> Dict[str, Any]:
    """Controlar clorador: 'on', 'off', 'auto'"""
    if accion.lower() == "on":
        return api_client.turn_chlorinator_on()
    elif accion.lower() == "off":
        return api_client.turn_chlorinator_off()
    elif accion.lower() == "auto":
        return api_client.set_automatic_mode()
    else:
        return {"success": False, "error": "invalid_action", "message": f"Acción inválida: {accion}"}


def verificar_conexion_api() -> bool:
    """Verificar si podemos conectar con FastAPI"""
    return api_client.is_api_available()


# Función de prueba
if __name__ == "__main__":
    print("🧪 Probando cliente API...")

    # Verificar conexión
    if verificar_conexion_api():
        print("✅ API disponible")

        # Probar obtener datos
        datos = cargar_datos_sensores()
        print(f"📊 Datos obtenidos: {datos.get('success', False)}")

        # Probar estado del sistema
        estado = obtener_estado_sistema()
        print(f"🔍 Estado sistema: {estado.get('success', False)}")

    else:
        print("❌ API no disponible - ¿Está ejecutándose FastAPI en puerto 8000?")
        print("💡 Para iniciar: python main.py")