"""
Dashboard Corregido para Sistema Asada Tsa Diglo Wak
Todas las propiedades corregidas para Reflex 0.8.4
"""

import reflex as rx
import requests
from datetime import datetime

# URL base de la API
API_BASE_URL = "http://localhost:8000"


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
            response = requests.get(f"{API_BASE_URL}/api/readings", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    readings = data.get("readings", [])

                    for reading in readings:
                        if reading["tank_id"] == "tank_a":
                            self.tank_a_level = reading.get("water_level_cm", 0)
                            self.tank_a_percent = reading.get("water_level_percent", 0)
                            self.tank_a_volume = reading.get("water_volume_m3", 0)
                            self.pump_status = reading.get("pump_status", False)
                        elif reading["tank_id"] == "tank_b":
                            self.tank_b_level = reading.get("water_level_cm", 0)
                            self.tank_b_percent = reading.get("water_level_percent", 0)
                            self.tank_b_volume = reading.get("water_volume_m3", 0)
                            self.chlorine_ppm = reading.get("chlorine_ppm", 0)
                            self.chlorine_status = reading.get("chlorine_status", "unknown")
                            self.chlorinator_status = reading.get("chlorinator_status", False)

                    self.api_connected = True
                    self.last_update = datetime.now().strftime("%H:%M:%S")
                    self.message = "✅ Datos actualizados correctamente"
                else:
                    self.api_connected = False
                    self.message = "❌ Error en respuesta de API"
            else:
                self.api_connected = False
                self.message = f"❌ Error HTTP: {response.status_code}"

        except Exception as e:
            self.api_connected = False
            self.message = f"❌ Error de conexión: {str(e)}"

        self.loading = False

    def pump_on(self):
        """Encender bomba"""
        try:
            response = requests.post(f"{API_BASE_URL}/api/control/pump/on", timeout=5)
            if response.status_code == 200:
                self.message = "🟢 Bomba encendida exitosamente"
                self.load_data()
            else:
                self.message = "❌ Error encendiendo bomba"
        except Exception as e:
            self.message = f"❌ Error: {str(e)}"

    def pump_off(self):
        """Apagar bomba"""
        try:
            response = requests.post(f"{API_BASE_URL}/api/control/pump/off", timeout=5)
            if response.status_code == 200:
                self.message = "🔴 Bomba apagada exitosamente"
                self.load_data()
            else:
                self.message = "❌ Error apagando bomba"
        except Exception as e:
            self.message = f"❌ Error: {str(e)}"

    def chlorinator_on(self):
        """Encender clorador"""
        try:
            response = requests.post(f"{API_BASE_URL}/api/control/chlorinator/on", timeout=5)
            if response.status_code == 200:
                self.message = "🟢 Clorador encendido exitosamente"
                self.load_data()
            else:
                self.message = "❌ Error encendiendo clorador"
        except Exception as e:
            self.message = f"❌ Error: {str(e)}"

    def chlorinator_off(self):
        """Apagar clorador"""
        try:
            response = requests.post(f"{API_BASE_URL}/api/control/chlorinator/off", timeout=5)
            if response.status_code == 200:
                self.message = "🔴 Clorador apagado exitosamente"
                self.load_data()
            else:
                self.message = "❌ Error apagando clorador"
        except Exception as e:
            self.message = f"❌ Error: {str(e)}"

    def auto_mode(self):
        """Activar modo automático"""
        try:
            response = requests.post(f"{API_BASE_URL}/api/control/auto", timeout=5)
            if response.status_code == 200:
                self.message = "🤖 Modo automático activado"
                self.load_data()
            else:
                self.message = "❌ Error activando modo automático"
        except Exception as e:
            self.message = f"❌ Error: {str(e)}"


def dashboard() -> rx.Component:
    """Dashboard principal con mejoras visuales"""
    return rx.box(
        # Fondo con gradiente
        rx.container(
            # Encabezado elegante con banner
            rx.box(
                rx.vstack(
                    # Logo y título principal con efecto
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
                                text_shadow="3px 3px 6px rgba(0,0,0,0.5)",
                                font_weight="800",
                                letter_spacing="1px",
                            ),
                            rx.text(
                                "Sistema de Monitoreo y Control de Tanques",
                                size="4",
                                color="rgba(255,255,255,0.9)",
                                text_shadow="2px 2px 4px rgba(0,0,0,0.4)",
                                font_style="italic",
                                letter_spacing="0.5px",
                            ),
                            align_items="start",
                        ),
                        align_items="center",
                    ),

                    # Línea decorativa
                    rx.box(
                        width="300px",
                        height="3px",
                        background="linear-gradient(90deg, transparent, rgba(255,255,255,0.8), transparent)",
                        border_radius="2px",
                    ),

                    # Subtítulo adicional
                    rx.text(
                        "🏛️ Comunidad Indígena Cabécar • 🌊 Gestión Inteligente del Agua",
                        color="rgba(255,255,255,0.8)",
                        font_size="1.1em",
                        text_align="center",
                        font_weight="500",
                    ),

                    align_items="center",
                ),
                padding="2.5rem",
                bg="rgba(0, 0, 0, 0.15)",
                border="1px solid rgba(255,255,255,0.2)",
                border_radius="20px",
                margin_bottom="2rem",
                backdrop_filter="blur(15px)",
                box_shadow="0 8px 32px rgba(0,0,0,0.3)",
            ),

            # Barra de estado mejorada
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
                        text_align="center"
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

            # Grid de tarjetas del mismo tamaño
            rx.grid(
                # Tanque A - Tarjeta uniforme
                rx.box(
                    rx.vstack(
                        # Header de la tarjeta
                        rx.hstack(
                            rx.text("🏛️", font_size="2em"),
                            rx.vstack(
                                rx.heading("Tanque A", size="4", color="white"),
                                rx.text("Cisterna", color="rgba(255,255,255,0.7)", font_size="0.9em"),
                                align_items="start",
                            ),
                            justify="start",
                            align_items="center",
                            width="100%",
                        ),

                        # Separador
                        rx.divider(color="rgba(255,255,255,0.2)"),

                        # Datos principales
                        rx.vstack(
                            rx.text(
                                "Nivel: ", DashboardState.tank_a_percent, "%",
                                font_size="1.8em",
                                font_weight="bold",
                                color="#3b82f6",
                                text_align="center"
                            ),
                            rx.text("Altura: ", DashboardState.tank_a_level, " cm", color="rgba(255,255,255,0.8)"),
                            rx.text("Volumen: ", DashboardState.tank_a_volume, " m³", color="rgba(255,255,255,0.8)"),
                            align_items="center",
                        ),

                        # Separador
                        rx.divider(color="rgba(255,255,255,0.2)"),

                        # Estado del equipo
                        rx.vstack(
                            rx.text("Estado Bomba:", font_weight="bold", color="white", font_size="1.1em"),
                            rx.cond(
                                DashboardState.pump_status,
                                rx.text("🟢 ENCENDIDA", color="#22c55e", font_weight="bold", font_size="1.1em"),
                                rx.text("🔴 APAGADA", color="#ef4444", font_weight="bold", font_size="1.1em")
                            ),
                            align_items="center",
                        ),

                        align_items="center",
                        height="100%",
                        justify="between",
                    ),
                    padding="2rem",
                    bg="rgba(59, 130, 246, 0.1)",
                    border="2px solid rgba(59, 130, 246, 0.3)",
                    border_radius="16px",
                    backdrop_filter="blur(10px)",
                    height="400px",
                    width="100%",
                ),

                # Tanque B - Tarjeta uniforme
                rx.box(
                    rx.vstack(
                        # Header de la tarjeta
                        rx.hstack(
                            rx.text("🏗️", font_size="2em"),
                            rx.vstack(
                                rx.heading("Tanque B", size="4", color="white"),
                                rx.text("150m³", color="rgba(255,255,255,0.7)", font_size="0.9em"),
                                align_items="start",
                            ),
                            justify="start",
                            align_items="center",
                            width="100%",
                        ),

                        # Separador
                        rx.divider(color="rgba(255,255,255,0.2)"),

                        # Datos principales
                        rx.vstack(
                            rx.text(
                                "Nivel: ", DashboardState.tank_b_percent, "%",
                                font_size="1.8em",
                                font_weight="bold",
                                color="#10b981",
                                text_align="center"
                            ),
                            rx.text("Altura: ", DashboardState.tank_b_level, " cm", color="rgba(255,255,255,0.8)"),
                            rx.text("Volumen: ", DashboardState.tank_b_volume, " m³", color="rgba(255,255,255,0.8)"),
                            align_items="center",
                        ),

                        # Información de cloro
                        rx.vstack(
                            rx.text("🧪 Cloro: ", DashboardState.chlorine_ppm, " ppm", color="#06b6d4",
                                    font_weight="bold"),
                            rx.text("Estado: ", DashboardState.chlorine_status, text_transform="uppercase",
                                    color="rgba(255,255,255,0.8)"),
                            rx.cond(
                                DashboardState.chlorinator_status,
                                rx.text("🟢 CLORADOR ACTIVO", color="#22c55e", font_weight="bold"),
                                rx.text("🔴 CLORADOR INACTIVO", color="#ef4444", font_weight="bold")
                            ),
                            align_items="center",
                        ),

                        align_items="center",
                        height="100%",
                        justify="between",
                    ),
                    padding="2rem",
                    bg="rgba(16, 185, 129, 0.1)",
                    border="2px solid rgba(16, 185, 129, 0.3)",
                    border_radius="16px",
                    backdrop_filter="blur(10px)",
                    height="400px",
                    width="100%",
                ),

                # Panel de Controles - Tarjeta uniforme
                rx.box(
                    rx.vstack(
                        # Header de la tarjeta
                        rx.hstack(
                            rx.text("🎛️", font_size="2em"),
                            rx.vstack(
                                rx.heading("Controles", size="4", color="white"),
                                rx.text("Manuales", color="rgba(255,255,255,0.7)", font_size="0.9em"),
                                align_items="start",
                            ),
                            justify="start",
                            align_items="center",
                            width="100%",
                        ),

                        # Separador
                        rx.divider(color="rgba(255,255,255,0.2)"),

                        # Controles de Bomba
                        rx.vstack(
                            rx.text("💧 Bomba", font_weight="bold", color="white", font_size="1.1em"),
                            rx.button(
                                "🟢 ENCENDER",
                                on_click=DashboardState.pump_on,
                                bg="rgba(34, 197, 94, 0.8)",
                                color="white",
                                size="3",
                                width="90%",
                                border="1px solid rgba(255,255,255,0.2)",
                            ),
                            rx.button(
                                "🔴 APAGAR",
                                on_click=DashboardState.pump_off,
                                bg="rgba(239, 68, 68, 0.8)",
                                color="white",
                                size="3",
                                width="90%",
                                border="1px solid rgba(255,255,255,0.2)",
                            ),
                            align_items="center",
                        ),

                        # Controles de Clorador
                        rx.vstack(
                            rx.text("🧪 Clorador", font_weight="bold", color="white", font_size="1.1em"),
                            rx.button(
                                "🟢 ENCENDER",
                                on_click=DashboardState.chlorinator_on,
                                bg="rgba(59, 130, 246, 0.8)",
                                color="white",
                                size="3",
                                width="90%",
                                border="1px solid rgba(255,255,255,0.2)",
                            ),
                            rx.button(
                                "🔴 APAGAR",
                                on_click=DashboardState.chlorinator_off,
                                bg="rgba(147, 51, 234, 0.8)",
                                color="white",
                                size="3",
                                width="90%",
                                border="1px solid rgba(255,255,255,0.2)",
                            ),
                            align_items="center",
                        ),

                        # Modo Automático
                        rx.button(
                            "🤖 AUTOMÁTICO",
                            on_click=DashboardState.auto_mode,
                            bg="rgba(245, 158, 11, 0.8)",
                            color="white",
                            size="3",
                            width="90%",
                            border="1px solid rgba(255,255,255,0.2)",
                        ),

                        align_items="center",
                        height="100%",
                        justify="between",
                    ),
                    padding="2rem",
                    bg="rgba(107, 114, 128, 0.1)",
                    border="2px solid rgba(107, 114, 128, 0.3)",
                    border_radius="16px",
                    backdrop_filter="blur(10px)",
                    height="400px",
                    width="100%",
                ),

                columns="3",
                gap="2rem",
                width="100%",
            ),

            # Footer elegante centrado
            rx.center(
                # Footer elegante con información completa
                rx.box(
                    rx.vstack(
                        # Línea decorativa superior
                        rx.box(
                            width="400px",
                            height="2px",
                            background="linear-gradient(90deg, transparent, rgba(255,255,255,0.6), transparent)",
                            border_radius="1px",
                        ),

                        # Información principal
                        rx.vstack(
                            rx.text(
                                "© 2025 Asada Tsa Diglo Wak",
                                color="white",
                                font_weight="600",
                                font_size="1.1em",
                                text_shadow="1px 1px 2px rgba(0,0,0,0.5)",
                            ),
                            rx.text(
                                "Proyecto Final • Técnico en Programación Asistida con IA",
                                color="rgba(255,255,255,0.8)",
                                font_size="0.95em",
                                text_align="center",
                            ),
                            rx.text(
                                "👨‍💻 Desarrollado por Sandro Uva Fernández",
                                color="rgba(255,255,255,0.9)",
                                font_size="1em",
                                font_weight="500",
                                text_shadow="1px 1px 2px rgba(0,0,0,0.4)",
                            ),
                            align_items="center",
                        ),

                        # Información técnica
                        rx.hstack(
                            rx.text("🐍 Python", color="rgba(255,255,255,0.7)", font_size="0.9em"),
                            rx.text("•", color="rgba(255,255,255,0.5)"),
                            rx.text("⚡ Reflex", color="rgba(255,255,255,0.7)", font_size="0.9em"),
                            rx.text("•", color="rgba(255,255,255,0.5)"),
                            rx.text("🔧 FastAPI", color="rgba(255,255,255,0.7)", font_size="0.9em"),
                            rx.text("•", color="rgba(255,255,255,0.5)"),
                            rx.text("🌐 PyCharm", color="rgba(255,255,255,0.7)", font_size="0.9em"),
                            justify="center",
                        ),

                        align_items="center",
                    ),
                    padding="2rem",
                    bg="rgba(0, 0, 0, 0.1)",
                    border="1px solid rgba(255,255,255,0.1)",
                    border_radius="16px",
                    margin_top="3rem",
                    backdrop_filter="blur(10px)",
                    width="100%",
                    max_width="600px",
                ),
            ),

            padding="2rem",
            max_width="1400px",
            margin="0 auto",
        ),

        # Fondo con gradiente
        background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        min_height="100vh",
        width="100%",
    )


# Crear la aplicación
app = rx.App()
app.add_page(dashboard, route="/", title="Asada Tsa Diglo Wak")