import io
import requests
from PIL import Image, ImageDraw, ImageFilter, ImageOps

url = 'https://image.tmdb.org/t/p/w1280/lyQBXzOQSuE59IsHyhrp0qIiPAz.jpg' # Shawshank poster
response = requests.get(url)
img_data = Image.open(io.BytesIO(response.content)).convert("RGBA")

target_width = 1000
target_height = 350

# 1. Create blurred background
bg = ImageOps.fit(img_data, (target_width, target_height), method=Image.Resampling.LANCZOS)
bg = bg.filter(ImageFilter.GaussianBlur(radius=30))

# 2. Resize original poster to fit height exactly
poster_height = target_height
poster_width = int((img_data.width / img_data.height) * poster_height)
poster = img_data.resize((poster_width, poster_height), Image.Resampling.LANCZOS)

# 3. Paste poster onto right side of blurred bg
# We want it aligned to the right but maybe 50px padding from the right
paste_x = target_width - poster_width - 80
bg.paste(poster, (paste_x, 0), mask=poster)

# 4. Apply fade gradient (Dark on left, fading to transparent on right)
gradient = Image.new('L', (target_width, target_height), color=0)
draw = ImageDraw.Draw(gradient)

# We want the left 50% to be pure black, and then fade out to transparent over the poster
for x in range(target_width):
    if x < target_width * 0.4:
        alpha = 255
    else:
        # Fade from 255 to 0 between 40% and 90%
        progress = (x - target_width * 0.4) / (target_width * 0.5)
        alpha = int(255 * max(0.0, min(1.0, 1.0 - progress)))
    draw.line((x, 0, x, target_height), fill=alpha)

overlay = Image.new('RGBA', (target_width, target_height), color=(14, 14, 16, 255))
overlay.putalpha(gradient)
bg = Image.alpha_composite(bg, overlay)

bg.save("test_banner.png")
print("Saved test_banner.png")
