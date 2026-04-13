import io
import threading
import requests
from PIL import Image, ImageDraw
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import QObject, pyqtSignal, QByteArray


class _ImageSignalRelay(QObject):
    """Thread-safe signal relay for updating QLabel pixmaps from background threads."""
    image_ready = pyqtSignal(object, QPixmap)  # (widget, pixmap)


# Global singleton relay — lives on the main thread
_relay = _ImageSignalRelay()


def _on_image_ready(widget, pixmap):
    try:
        widget.setPixmap(pixmap)
    except RuntimeError:
        pass  # Widget was destroyed before image arrived


_relay.image_ready.connect(_on_image_ready)


class ImageManager:
    """Handles async downloading, caching, and styling of TMDB images for PyQt6."""
    
    _cache = {}

    @staticmethod
    def load_image_async(url, label_widget, is_banner=False, radius=0, target_width=None, target_height=None, bg_color=(10, 10, 15, 255)):
        cache_key = f"{url}_{is_banner}_{radius}_{target_width}x{target_height}"
        
        if cache_key in ImageManager._cache:
            try:
                label_widget.setPixmap(ImageManager._cache[cache_key])
            except RuntimeError:
                pass
            return

        def fetch():
            try:
                response = requests.get(url, timeout=8)
                if response.status_code != 200:
                    return
                    
                img_data = Image.open(io.BytesIO(response.content)).convert("RGBA")
                
                if is_banner and target_width and target_height:
                    from PIL import ImageFilter, ImageOps
                    # 1. Create blurred background
                    bg = ImageOps.fit(img_data, (target_width, target_height), method=Image.Resampling.LANCZOS)
                    bg = bg.filter(ImageFilter.GaussianBlur(radius=25))

                    # 2. Resize original poster correctly and paste
                    poster_h = target_height - 60
                    poster_w = int((img_data.width / img_data.height) * poster_h)
                    poster = img_data.resize((poster_w, poster_h), Image.Resampling.LANCZOS)
                    
                    # Add subtle shadow behind poster
                    shadow = Image.new('RGBA', bg.size, (0, 0, 0, 0))
                    draw_s = ImageDraw.Draw(shadow)
                    paste_x = target_width - poster_w - 60
                    paste_y = 30
                    draw_s.rectangle([paste_x-10, paste_y-10, paste_x+poster_w+10, paste_y+poster_h+10], fill=(0,0,0,150))
                    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
                    bg = Image.alpha_composite(bg, shadow)
                    
                    bg.paste(poster, (paste_x, paste_y), mask=poster)

                    # 3. Fade gradient (Dark left, transparent right)
                    gradient = Image.new('L', (target_width, target_height), color=0)
                    draw = ImageDraw.Draw(gradient)
                    for x in range(target_width):
                        if x < target_width * 0.4: alpha = 255
                        else: alpha = int(255 * max(0.0, min(1.0, 1.0 - ((x - target_width * 0.4) / (target_width * 0.4)))))
                        draw.line((x, 0, x, target_height), fill=alpha)

                    overlay = Image.new('RGBA', (target_width, target_height), color=bg_color)
                    overlay.putalpha(gradient)
                    img_data = Image.alpha_composite(bg, overlay)
                else:
                    if target_width and target_height:
                        img_data = img_data.resize((target_width, target_height), Image.Resampling.LANCZOS)
                    if radius > 0:
                        img_data = ImageManager._apply_rounded_corners(img_data, radius)

                # Convert PIL → QPixmap
                data = img_data.tobytes("raw", "RGBA")
                qim = QImage(data, img_data.width, img_data.height, img_data.width * 4, QImage.Format.Format_RGBA8888)
                pixmap = QPixmap.fromImage(qim)
                
                ImageManager._cache[cache_key] = pixmap
                
                # Thread-safe UI update via signal
                _relay.image_ready.emit(label_widget, pixmap)
                
            except Exception as e:
                print(f"[ImageManager] Failed to load {url}: {e}")

        threading.Thread(target=fetch, daemon=True).start()

    @staticmethod
    def _apply_fade_gradient(img):
        width, height = img.size
        gradient = Image.new('L', (width, height), color=0xFF)
        draw = ImageDraw.Draw(gradient)
        
        for y in range(height):
            alpha = int(255 * (1 - (y / height) ** 1.8))
            draw.line((0, y, width, y), fill=alpha)
            
        bg = Image.new('RGBA', (width, height), color=(10, 10, 15, 255))
        img.putalpha(gradient)
        return Image.alpha_composite(bg, img)

    @staticmethod
    def _apply_rounded_corners(img, radius):
        mask = Image.new('L', img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0) + img.size, radius=radius, fill=255)
        result = img.copy()
        result.putalpha(mask)
        return result
