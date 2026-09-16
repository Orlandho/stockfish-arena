"""
Generador del icono oficial de Stockfish Arena para Windows (.ico y .png).
Crea un icono de alta resolución con múltiples capas (16x16 hasta 256x256)
para accesos directos, barra de tareas y barra de título de la aplicación.
"""

import os
from PIL import Image, ImageDraw, ImageFont

def generate_icon(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    png_path = os.path.join(output_dir, "app_icon.png")
    ico_path = os.path.join(output_dir, "app_icon.ico")

    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Fondo squircle (cuadrado redondeado) moderno en gris grafito / oscuro
    margin = 24
    corner_radius = 110
    draw.rounded_rectangle(
        [(margin, margin), (size - margin, size - margin)],
        radius=corner_radius,
        fill="#1e2227",
        outline="#4caf50",
        width=12
    )

    # 2. Resplandor interno sutil
    draw.rounded_rectangle(
        [(margin + 16, margin + 16), (size - margin - 16, size - margin - 16)],
        radius=corner_radius - 12,
        outline="#2e7d32",
        width=4
    )

    # 3. Dibujar silueta estilizada de un Caballo de Ajedrez (Knight)
    # Coordenadas proporcionales en escala 512x512
    knight_points = [
        (256, 100), # Punta oreja
        (230, 115), # Base oreja
        (200, 150), # Frente
        (160, 210), # Hocico superior
        (150, 245), # Nariz
        (180, 270), # Labio inferior
        (225, 275), # Barbilla
        (240, 310), # Cuello frontal
        (200, 370), # Pecho
        (180, 410), # Base frontal
        (340, 410), # Base trasera
        (330, 340), # Crin inferior
        (355, 250), # Crin media
        (340, 180), # Crin superior
        (300, 130), # Nuca
        (270, 115), # Detrás de la oreja
    ]
    draw.polygon(knight_points, fill="#ffffff", outline="#000000")

    # Detalles del caballo: Ojo
    draw.ellipse([(205, 195), (225, 215)], fill="#1e2227")
    draw.ellipse([(212, 202), (218, 208)], fill="#ffffff")

    # Detalle de la crin y corte
    draw.line([(260, 160), (320, 200)], fill="#1e2227", width=6)
    draw.line([(250, 220), (330, 260)], fill="#1e2227", width=6)
    draw.line([(240, 280), (310, 320)], fill="#1e2227", width=6)

    # Base del pedestal
    draw.rounded_rectangle([(160, 410), (360, 435)], radius=10, fill="#ffffff", outline="#000000", width=4)

    # 4. Guardar PNG maestro de 512x512
    img.save(png_path, format="PNG")
    print(f"Icono PNG maestro guardado en: {png_path}")

    # 5. Guardar ICO con múltiples resoluciones (16, 24, 32, 48, 64, 128, 256)
    ico_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)]
    img.save(ico_path, format="ICO", sizes=ico_sizes)
    print(f"Icono Windows ICO guardado en: {ico_path}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    generate_icon(current_dir)
