from PIL import Image

# Create a transparent image with the correct dimensions for Roblox shirt template
img = Image.new('RGBA', (585, 559), (0, 0, 0, 0))
img.save('src/assets/shirt_template.png')