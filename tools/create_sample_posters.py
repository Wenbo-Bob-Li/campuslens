"""Generate original typography-only poster fixtures for CampusLens.

These deliberately fictional posters exercise image input, building matching,
and missing-location handling. They contain no third-party logos or photos.
Run from any directory with the project's configured Python interpreter.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "static" / "samples"
WIDTH, HEIGHT = 1100, 1500
INK = "#152c31"
MUTED = "#4c686c"
BACKGROUND = "#f4f7f1"
ACCENT = "#e5f267"


def font(size: int, bold: bool = False):
    names = (
        ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf", "DejaVuSans-Bold.ttf"]
        if bold
        else ["C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf", "DejaVuSans.ttf"]
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def lines_for(draw, value, text_font, max_width):
    """Wrap text by rendered width so the fixtures stay legible."""
    lines = []
    for paragraph in value.split("\n"):
        current = ""
        for word in paragraph.split():
            candidate = f"{current} {word}".strip()
            if current and draw.textbbox((0, 0), candidate, font=text_font)[2] > max_width:
                lines.append(current)
                current = word
            else:
                current = candidate
        lines.append(current)
    return lines


def text_block(draw, value, y, size, *, bold=False, fill=INK, gap=12):
    text_font = font(size, bold)
    for line in lines_for(draw, value, text_font, WIDTH - 144):
        draw.text((72, y), line, font=text_font, fill=fill)
        box = draw.textbbox((0, 0), line or "Ag", font=text_font)
        y += max(size, box[3] - box[1]) + gap
    return y


def poster(filename, title, when, location, description):
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, WIDTH, 22), fill=INK)
    draw.rounded_rectangle((58, 70, WIDTH - 58, 154), radius=16, fill=ACCENT)
    draw.text((80, 89), "SAMPLE / FICTIONAL EVENT", font=font(38, True), fill=INK)
    y = text_block(draw, title, 215, 88, bold=True, gap=16)
    y += 50
    draw.line((72, y, WIDTH - 72, y), fill="#c7d4ca", width=3)
    y += 44
    y = text_block(draw, "WHEN", y, 25, bold=True, fill=MUTED)
    y = text_block(draw, when, y + 4, 44, bold=True)
    y = text_block(draw, "WHERE", y + 38, 25, bold=True, fill=MUTED)
    y = text_block(draw, location, y + 4, 44, bold=True)
    y = text_block(draw, description, y + 48, 34, fill=MUTED, gap=14)
    y = text_block(draw, "Free · Open to students", y + 30, 34, bold=True)
    text_block(draw, "Hosted by CampusLens Demo", y + 24, 31, fill=MUTED)
    draw.line((72, 1320, WIDTH - 72, 1320), fill="#c7d4ca", width=3)
    text_block(draw, "Original demo fixture. This is not a real event.", 1356, 25, fill=MUTED)
    text_block(draw, "No year, date, or time zone is implied.", 1402, 25, fill=MUTED)
    image.save(OUTPUT / filename, optimize=True)
    return image


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    full = poster(
        "campus-creators.png",
        "Campus Creators Meetup",
        "Friday · 4:00–6:00 PM",
        "Price Center — West Ballroom",
        "Meet other campus creators. Share a project and exchange ideas.",
    )
    full.save(OUTPUT / "campus-creators.jpg", quality=92, optimize=True)
    poster(
        "ai-study-jam.png",
        "Campus AI Study Jam",
        "Saturday · 2:00–4:00 PM",
        "Design and Innovation Building (DIB), Room 208",
        "Bring a question. Learn together and explore small AI projects.",
    )
    poster(
        "location-pending.png",
        "Campus Community Exchange",
        "Sunday · 11:00 AM",
        "Location to be announced",
        "Share ideas for a more connected campus. Venue details will follow.",
    )
    print(f"Created 3 fictional PNG posters and 1 JPEG in {OUTPUT}")


if __name__ == "__main__":
    main()
