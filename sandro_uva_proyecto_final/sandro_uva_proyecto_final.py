"""
Dashboard para Sistema Asada Tsa Diglo Wak
Reflex 0.8.4
- API_BASE_URL por variable de entorno (para cloud)
- Requests con timeout
"""

import os
import reflex as rx
import requests
from datetime import datetime

# ✅ API base URL:
# - Local: http://localhost:8000
# - Cloud: setear en Reflex Cloud (Settings -> Environment Variables)
API_BASE_URL = os.getenv("API_BASE_URL", "").rstrip("/")


class DashboardState(rx.State):
    """Estado principal del dashboard"""

    # Datos de los tanques
    tank_a_level: float = 0.0
    tank_a_percent: float = 0.0
    tank_a_volume: float = 0.0
    pump_status: bool = False

    tank_b_level: float = 0.0
    tank_b_percent: float = 0.0
    tank_b_volume: float = 0.0
    chlorine_ppm: float = 0.0
    chlorine_status: str = "unknown"
    chlorinator_status: bool = False

    # Estado del sistema
    api_connected: bool = False
    last_update: str = ""
    loading: bool = False
    message: str = "Presiona 'Cargar Datos' para comenzar"

    def load_data(self):
        """Cargar datos de la API"""
        self.loading = True
        try:
            url = f"{API_BASE_URL}/api/readings"
            response = requests.get(url, timeout=8)

            if response.status_code == 200:
                data = response.json()

                if data.get("success"):
                    readings = data.get("readings", [])

                    for reading in readings:
                        if reading.get("tank_id") == "tank_a":
                            self.tank_a_level = float(reading.get("water_level_cm", 0) or 0)
                            self.tank_a_percent = float(reading.get("water_level_percent", 0) or 0)
                            self.tank_a_volume = float(reading.get("water_volume_m3", 0) or 0)
                            self.pump_status = bool(reading.get("pump_status", False))

                        elif reading.get("tank_id") == "tank_b":
                            self.tank_b_level = float(reading.get("water_level_cm", 0) or 0)
                            self.tank_b_percent = float(reading.get("water_level_percent", 0) or 0)
                            self.tank_b_volume = float(reading.get("water_volume_m3", 0) or 0)
                            self.chlorine_ppm = float(reading.get("chlorine_ppm", 0) or 0)
                            self.chlorine_status = str(reading.get("chlorine_status", "unknown"))
                            self.chlorinator_status = bool(reading.get("chlorinator_status", False))

                    self.api_connected = True
                    self.last_update = datetime.now().strftime("%H:%M:%S")
                    self.message = "✅ Datos actualizados correctamente"
                else:
                    self.api_connected = False
                    self.message = "❌ La API respondió pero success=false"

            else:
                self.api_connected = False
                self.message = f"❌ Error HTTP: {response.status_code}"

        except Exception as e:
            self.api_connected = False
            self.message = f"❌ Error de conexión: {str(e)}"

        self.loading = False

    def pump_on(self):
        try:
            response = requests.post(f"{API_BASE_URL}/api/control/pump/on", timeout=8)
            if response.status_code == 200:
                self.message = "🟢 Bomba encendida exitosamente"
                self.load_data()
            else:
                self.message = f"❌ Error encendiendo bomba ({response.status_code})"
        except Exception as e:
            self.message = f"❌ Error: {str(e)}"

    def pump_off(self):
        try:
            response = requests.post(f"{API_BASE_URL}/api/control/pump/off", timeout=8)
            if response.status_code == 200:
                self.message = "🔴 Bomba apagada exitosamente"
                self.load_data()
            else:
                self.message = f"❌ Error apagando bomba ({response.status_code})"
        except Exception as e:
            self.message = f"❌ Error: {str(e)}"

    def chlorinator_on(self):
        try:
            response = requests.post(f"{API_BASE_URL}/api/control/chlorinator/on", timeout=8)
            if response.status_code == 200:
                self.message = "🟢 Clorador encendido exitosamente"
                self.load_data()
            else:
                self.message = f"❌ Error encendiendo clorador ({response.status_code})"
        except Exception as e:
            self.message = f"❌ Error: {str(e)}"

    def chlorinator_off(self):
        try:
            response = requests.post(f"{API_BASE_URL}/api/control/chlorinator/off", timeout=8)
            if response.status_code == 200:
                self.message = "🔴 Clorador apagado exitosamente"
                self.load_data()
            else:
                self.message = f"❌ Error apagando clorador ({response.status_code})"
        except Exception as e:
            self.message = f"❌ Error: {str(e)}"

    def auto_mode(self):
        try:
            response = requests.post(f"{API_BASE_URL}/api/control/auto", timeout=8)
            if response.status_code == 200:
                self.message = "🤖 Modo automático activado"
                self.load_data()
            else:
                self.message = f"❌ Error activando modo automático ({response.status_code})"
        except Exception as e:
            self.message = f"❌ Error: {str(e)}"


def dashboard() -> rx.Component:
    return rx.box(
        rx.container(
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.box(
                            rx.text("💧", font_size="4em", color="#60a5fa"),
                            padding="1rem",
                            bg="rgba(255,255,255,0.1)",
                            border_radius="50%",
                            border="2px solid rgba(255,255,255,0.3)",
                        ),
                        rx.vstack(
                            rx.heading(
                                "Asada Tsa Diglo Wak",
                                size="6",
                                color="white",
                                font_weight="800",
                            ),
                            rx.text(
                                "Sistema de Monitoreo y Control de Tanques",
                                size="4",
                                color="rgba(255,255,255,0.9)",
                                font_style="italic",
                            ),
                            align_items="start",
                        ),
                        align_items="center",
                    ),
                    rx.text(
                        "🏛️ Comunidad Indígena Cabécar • 🌊 Gestión Inteligente del Agua",
                        color="rgba(255,255,255,0.8)",
                        font_size="1.1em",
                        text_align="center",
                    ),
                    align_items="center",
                ),
                padding="2.5rem",
                bg="rgba(0, 0, 0, 0.15)",
                border="1px solid rgba(255,255,255,0.2)",
                border_radius="20px",
                margin_bottom="2rem",
                backdrop_filter="blur(15px)",
            ),

            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.text("🌐 Estado API:", font_weight="bold", color="white"),
                        rx.cond(
                            DashboardState.api_connected,
                            rx.text("✅ Conectada", color="#4ade80", font_weight="bold"),
                            rx.text("❌ Desconectada", color="#ef4444", font_weight="bold"),
                        ),
                        rx.text("⏰", color="white"),
                        rx.text(DashboardState.last_update, color="rgba(255,255,255,0.8)"),
                        justify="center",
                        align_items="center",
                    ),
                    rx.button(
                        "🔄 Cargar Datos",
                        on_click=DashboardState.load_data,
                        loading=DashboardState.loading,
                        bg="rgba(59, 130, 246, 0.8)",
                        color="white",
                        size="3",
                        border="1px solid rgba(255,255,255,0.2)",
                    ),
                    rx.text(
                        DashboardState.message,
                        color="#60a5fa",
                        font_style="italic",
                        text_align="center",
                    ),
                    rx.text(
                        f"API: {API_BASE_URL}",
                        color="rgba(255,255,255,0.6)",
                        font_size="0.85em",
                    ),
                    align_items="center",
                ),
                padding="1.5rem",
                bg="rgba(0, 0, 0, 0.2)",
                border="1px solid rgba(255,255,255,0.1)",
                border_radius="12px",
                margin_bottom="2rem",
                backdrop_filter="blur(10px)",
            ),

            # (tu grid y footer pueden quedarse igual; no los toqué para no romper diseño)
            # Si querés, luego pegamos el resto exacto sin cambios.

            padding="2rem",
            max_width="1400px",
            margin="0 auto",
        ),
        background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        min_height="100vh",
        width="100%",
    )


app = rx.App()
app.add_page(dashboard, route="/", title="Asada Tsa Diglo Wak")

