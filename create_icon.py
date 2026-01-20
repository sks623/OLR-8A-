"""Create a simple placeholder icon for OLR 8A"""
from PIL import Image, ImageDraw, ImageFont
import os

# Create multiple sizes for ICO
sizes = [256, 128, 64, 48, 32, 16]
images = []

for size in sizes:
    # Create a new image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw a rounded rectangle background (blue color)
    margin = int(size * 0.05)
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=int(size * 0.15),
        fill=(41, 128, 185, 255)  # Nice blue color
    )

    # Add text 'OLR'
    text = 'OLR'
    try:
        # Try to use a nice font
        font_size = int(size * 0.35)
        font = ImageFont.truetype('arial.ttf', font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center the text
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - int(size * 0.05)

    # Draw text in white
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

    images.append(img)

# Save as ICO
icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
images[0].save(icon_path, format='ICO', sizes=[(s, s) for s in sizes], append_images=images[1:])
print(f'Icon created: {icon_path}')
print(f'Sizes: {sizes}')
