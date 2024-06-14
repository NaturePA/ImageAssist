from PIL import Image

# Create a new transparent image
img = Image.new('RGBA', (184, 184), (0, 0, 0, 0))

# Save the image
img.save('transparent_184x184.png')
