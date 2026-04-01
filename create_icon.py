"""Create icon for Energy Post integration."""
from PIL import Image, ImageDraw, ImageFont

size = 256
img = Image.new('RGB', (size, size), '#1a1a2e')
draw = ImageDraw.Draw(img)

center_x = size // 2
center_y = size // 2

draw.ellipse([20, 20, size-20, size-20], fill='#2a2a3e', outline='#00d4ff', width=8)

sun_radius = 35
sun_x = center_x - 40
sun_y = center_y - 40
draw.ellipse(
    [sun_x - sun_radius, sun_y - sun_radius, sun_x + sun_radius, sun_y + sun_radius],
    fill='#ffd700'
)

for i in range(8):
    import math
    angle = i * (2 * math.pi / 8)
    start_x = sun_x + int(math.cos(angle) * (sun_radius + 5))
    start_y = sun_y + int(math.sin(angle) * (sun_radius + 5))
    end_x = sun_x + int(math.cos(angle) * (sun_radius + 15))
    end_y = sun_y + int(math.sin(angle) * (sun_radius + 15))
    draw.line([start_x, start_y, end_x, end_y], fill='#ffd700', width=4)

bolt_points = [
    (center_x + 20, center_y - 20),
    (center_x + 35, center_y + 10),
    (center_x + 25, center_y + 10),
    (center_x + 40, center_y + 50),
    (center_x + 15, center_y + 15),
    (center_x + 25, center_y + 15),
]
draw.polygon(bolt_points, fill='#00d4ff')

bar_width = 12
bar_spacing = 18
bar_heights = [30, 50, 40, 60]
start_x = center_x - 60

for i, height in enumerate(bar_heights):
    x = start_x + i * bar_spacing
    y = center_y + 50
    draw.rectangle(
        [x, y - height, x + bar_width, y],
        fill='#4ecdc4'
    )

img.save('c:\\dev\\projects\\ha-energy-post\\custom_components\\energy_post\\icon.png', 'PNG')
print("Icon created successfully!")
