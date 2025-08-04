import reflex as rx

config = rx.Config(
    app_name="sandro_uva_proyecto_final",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)