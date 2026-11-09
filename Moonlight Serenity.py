
""" Moonlight Serenity """

"""
A calm, no-pressure night sky game for relieving stress

Author: Prodipta Acharjee (github.com/serendurious-dev)
License: MIT

"""

import os
import math
import datetime
from array import array
import random
import pygame

# SETUP AND SETTINGS

pygame.init()

WIDTH = 1280
HEIGHT = 720
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Moonlight Serenity")
clock = pygame.time.Clock()
pygame.mouse.set_visible(False)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MUSIC_PATH = os.path.join(BASE_DIR, "music.mp3")
MUSIC_VOLUME = 0.35

# Coloring~

SKY_TOP = (3, 5, 16)
SKY_MIDDLE = (10, 17, 44)
SKY_HORIZON = (36, 40, 78)
TEXT_COLOR = (226, 230, 248)
STAR_TINTS = [(255, 255, 255), (205, 220, 255), (255, 238, 210), (225, 212, 255)]
GLOW_COLORS = [(170, 210, 255), (255, 200, 228), (198, 184, 255), (150, 236, 220), (255, 228, 180)]

FONT = pygame.font.SysFont("georgia", 20)
SMALL_FONT = pygame.font.SysFont("georgia", 16)
TITLE_FONT = pygame.font.SysFont("georgia", 30, italic = True)

CATCH_RADIUS = 34               # how close the wisp must be to touch any stars
TRAIL_LENGTH = 20               # how many past positions a shooting star remembers
STARS_PER_CONSTELLATION = 8     # catches needed to reveal the next constellation
REVEAL_FRAMES = 240             # 4 seconds for a constellation to draw itself
SUNRISE_FRAMES = 480            # 8 seconds for the sun rise

MISS_MESSAGES = [
    "The sky is still here, breathing with you.",
    "No worries, love. The night is still gentle.",
    "That star found its own way home",
    "Take your time. The stars will wait for you.",
    "Even missed stars are beautiful, so are you.",
]

# HELPING FUNCTIONS

def blend(color1, color2, t):
    """Mixing two colors, where, t = 0 means color1, t = 1 means color 2"""
    r = int(color1[0] + (color2[0] - color1[0]) * t)
    g = int(color1[1] + (color2[1] - color1[1]) * t)
    b = int(color1[2] + (color2[2] - color1[2]) * t)
    return (r, g, b)

def with_alpha(color, alpha):
    """Adding transparency value to (r, g, b) tuple -> (r, g, b, a)"""
    return color + (alpha,)

# Dictionary used as cache: key = (radius & color) tuple, value = glow image
# Each glow is drawn only once and then reused every frame (much faster)

glow_cache = {}

def get_glow(radius, color):
    """Returns a soft glow image"""
    key = (radius, color)
    if key not in glow_cache:
        glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for r in range(radius, 0, -1):
            strength = 1 - r / radius       # 0 at the edge, almost 1 in the centre
            alpha = int(255 * strength ** 2)
            pygame.draw.circle(glow, with_alpha(color, alpha), (radius, radius), r)
        glow_cache[key] = glow
    return glow_cache[key]

def draw_glow(surface, x, y, radius, color, alpha=255):
    """Drew a soft glow centered at (x, y)"""
    glow = get_glow(radius, color)
    glow.set_alpha(alpha)
    surface.blit(glow, (int(x) - radius, int(y) - radius))
    
def draw_text(surface, text, font, x, y, alpha = 255, center = False):
    """Texts on the screen"""
    image = font.render(text, True, TEXT_COLOR)
    image.set_alpha(alpha)
    rect = image.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(image, rect)
    
# THE NIGHT SKY - drawn once, reused every frame

def add_milky_way(sky):
    """Painted a faint diagonal band of haze and tiny stars"""
    start = (WIDTH * 0.05, HEIGHT)
    end = (WIDTH * 0.75, 0)
    
    # soft haze clouds along the band
    for i in range(45):
        t = random.random()
        x = start[0] + (end[0] - start[0]) * t + random.gauss(0, 40)
        y = start[1] + (end[1] - start[1]) * t + random.gauss(0, 40)
        draw_glow(sky, x, y, random.randint(70, 130), (110, 120, 180), random.randint(8, 16))
        
    # tiny dim stars packed inside the band
    for i in range(1600):
        t = random.random()
        x = int(start[0] + (end[0] - start[0]) * t + random.gauss(0, 50))
        y = int(start[1] + (end[1] - start[1]) * t + random.gauss(0, 50))
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            old = sky.get_at((x, y))
            sky.set_at((x, y), blend(old, random.choice(STAR_TINTS), random.uniform(0.15, 0.45)))
            
def add_dim_stars(sky, count):
    """Scatter faint single-pixel stars, few near horizon"""
    for i in range(count):
        x = random.randint(0, WIDTH - 1)
        y = int(random.random() ** 1.3 * HEIGHT * 0.95)
        old = sky.get_at((x, y))
        sky.set_at((x, y), blend(old, random.choice(STAR_TINTS), random.uniform(0.25, 0.7)))
        
def make_sky():
    """Creating background: three-colored gradient, milky way, dim stars"""
    sky = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        t = y / HEIGHT
        if t < 0.6:
            color = blend(SKY_TOP, SKY_MIDDLE, t / 0.6)
        else:
            color = blend(SKY_MIDDLE, SKY_HORIZON, (t - 0.6)/ 0.4)
        pygame.draw.line(sky, color, (0, y), (WIDTH, y))
    add_milky_way(sky)
    add_dim_stars(sky, 450)
    return sky

def make_twinkle_stars(count):
    """Creating stars that slowly twinkle.Each star is a dictionary"""
    stars = []
    for i in range(count):
        star = {
            "x": random.randint(0, WIDTH -1),
            "y": int(random.random() ** 1.4 * HEIGHT * 0.9),
            "color": random.choice(STAR_TINTS),
            "brightness": random.randint(110, 220),
            "phase": random.uniform(0, math.pi * 2),
            "speed": random.uniform(0.01, 0.04),
            "glow": random.choice([3, 4, 4, 5, 6]),
        }
        stars.append(star)
    return stars

def update_twinkle_stars(stars):
    for star in stars:
        star["phase"] += star["speed"]
        
def draw_twinkle_stars(surface, stars):
    for star in stars:
        alpha = star["brightness"] + math.sin(star["phase"]) * 60
        alpha = max(30, min(255, int(alpha)))
        draw_glow(surface, star["x"], star["y"], star["glow"], star["color"], alpha // 2)
        surface.set_at((star["x"], star["y"]), blend((0, 0, 0), star["color"], alpha / 255))
        
        
# MOON AND CLOUDS

MOON_X = WIDTH - 190
MOON_Y = 140
MOON_RADIUS = 50

# Darker sea on the moon (offset x, offset y, size) tuples

MOON_SEAS = [(-14, -8, 22), (12, -14, 15), (10, 12, 17), (-10, 18, 10)]

def make_moon_disc():
    """Drawing moon, with slightly darker edges and soft grey seas"""
    size = MOON_RADIUS * 2
    disc = pygame.Surface((size, size), pygame.SRCALPHA)
    for r in range(MOON_RADIUS, 0 , -1):
        t = r / MOON_RADIUS
        shade = int(250 - 30 * t ** 3)      # center = 250, edge = 220
        pygame.draw.circle(disc, (shade, shade - 4, shade - 14, 255), (MOON_RADIUS, MOON_RADIUS), r)
    for sea in MOON_SEAS:
        glow = get_glow(sea[2], (150, 148, 140))
        glow.set_alpha(55)
        disc.blit(glow, (MOON_RADIUS + sea[0] - sea[2], MOON_RADIUS + sea[1] - sea[2]))
    return disc

def draw_moon(surface, disc, pulse, light = 1.0):
    """Moon with a large soft halo which breathes slowly"""
    breathe = math.sin(pulse) * 8
    draw_glow(surface, MOON_X, MOON_Y, 200, (130, 145, 210), int((55 + breathe) * light))
    draw_glow(surface, MOON_X, MOON_Y, 95, (230, 225, 210), int((95 + breathe) * light))
    surface.blit(disc, (MOON_X - MOON_RADIUS, MOON_Y - MOON_RADIUS))
    
def make_cloud_image(width, height):
    """Building wispy clouds"""
    small_width = width // 6
    small_height = height // 6
    image = pygame.Surface((small_width, small_height), pygame.SRCALPHA)
    for i in range(9):
        r = random.randint(small_height // 3, small_height // 2)
        puff = pygame.transform.smoothscale(get_glow(r, (135, 145, 190)), (r * 5, r * 2))
        x = random.randint(0, small_width - r * 5)
        y = random.randint(0, small_height - r * 2)
        image.blit(puff, (x, y), special_flags = pygame.BLEND_RGBA_MAX)
    return pygame.transform.smoothscale(image, (width, height))

def make_cloud(start_on_screen = True):
    width = random.randint(380, 620)
    height = random.randint(90, 140)
    if start_on_screen:
        x = random.randint(-width, WIDTH)
    else:
        x = -width - random.randint(50, 300)
    cloud = {
        "image": make_cloud_image(width, height),
        "x": float(x),
        "y": random.randint(30, int(HEIGHT * 0.45)),
        "speed": random.uniform(0.08, 0.3),
        "alpha": random.randint(45, 80),
    }
    return cloud

def update_cloud(cloud):
    cloud["x"] += cloud["speed"]
    if cloud["x"] > WIDTH:          # drifted off the right side
        new_cloud = make_cloud(start_on_screen = False)
        cloud.update(new_cloud)     # reuse the same dictionary
        
def draw_cloud(surface, cloud):
    cloud["image"].set_alpha(cloud["alpha"])
    surface.blit(cloud["image"], (int(cloud["x"]), cloud["y"]))
    

# Soft Chimes- a musicbox note made from sine waves

CHIME_NOTES = [523.25, 587.33, 659.25, 783.99, 880.00, 1046.50]                 #C, D, E, G, A, and high C
CHIME_VOLUME = 0.22

def make_chime(freq):
    rate, size, channels = pygame.mixer.get_init()
    samples = array("h")                                                        # "h" - whole numbers that fit in 16 bits
    for i in range(int(rate * 1.4)):
        t = i / rate
        fade = math.exp(-t * 3.2) * min(1.0, t * 200)
        wave = math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(2 * math.pi * freq * 2 * t)
        value = int(wave / 1.3 * fade * 26000)
        for c in range(channels):
            samples.append(value)
    chime = pygame.mixer.Sound(buffer = samples)
    chime.set_valume(CHIME_VOLUME)
    return chime

def make_chimes():
    """Returns a list of notes, or an empty list if there is no sound"""
    if not pygame.mixer.get_init() or pygame.mixer.get_init()[1] != -16:
        return []
    return [make_chime(freq) for freq in CHIME_NOTES]

# REAL MOON PHASE- your moon matches the moon outside the window

SYNODIC_MONTH = 29.530588853                                                # days from one new moon to the next
KNOWN_NEW_MOON = datetime.datetime(2000, 1, 6, 18, 14, tzinfo = datetime.timezone.utc)
MOON_SHADOW = (16, 20, 40, 225)
PHASE_NAMES = ["new moon", "waxing crescent", "first quarter", "waxing gibbous", "full moon", "waning gibbous", "last quarter", "waning crescent"]

def get_moon_phase():
    """ 0 = new moon, 0.5 = full moon, almost 1 = new again"""
    now = datetime.datetime.now(datetime.timezone.utc)
    days = (now - KNOWN_NEW_MOON).total_seconds() / 86400
    return (days % SYNODIC_MONTH) / SYNODIC_MONTH

def phase_name(phase):
    return PHASE_NAMES[int(phase * 8 + 0.5) % 8]

def moon_brightness(phase):
    """How much moon is lit- 0 at new moon, 1 at full moon"""
    return(1 - math.cos(phase * 2 * math.pi)) / 2

def shade_moon(disc, phase):
    shadow = pygame.Surface(disc.get_size(), pygame.SRCALPHA)
    for row in range(-MOON_RADIUS, MOON_RADIUS):
        half = math.sqrt(MOON_RADIUS ** 2 - (row + 0.5) ** 2)
        edge = half * math.cos(phase * 2 * math.pi)
        if phase < 0.5:
            dark_from, dark_to = -half, edge
        else:
            dark_from, dark_to = -edge, half
        if dark_to > dark_from:
            y = MOON_RADIUS + row
            pygame.draw.line(shadow, MOON_SHADOW, (MOON_RADIUS + dark_from, y), (MOON_RADIUS + dark_to, y))
            
    disc.blit(shadow(0, 0))
    return disc

# Breathing guide- press B to  get breathe in for 4 sec, out for 6 sec

BREATHE_IN = 240
BREATHE_OUT = 360

def draw_breathing(surface, timer):
    cycle = timer % (BREATHE_IN + BREATHE_OUT)
    if cycle < BREATHE_IN:
        t = cycle / BREATHE_IN
        word = "breathe in..."
    else:
        t = 1 - (cycle - BREATHE_IN) / BREATHE_OUT
        word = "breathe out..."
    t = t * t * (3 - 2 * t)
    radius = int(40 + 70 * t)
    glow_radius = radius * 2 // 4 * 4
    draw_glow(surface, WIDTH // 2, HEIGHT // 2, glow_radius, (170, 200, 255), 70)
    pygame.draw.circle(surface, (200, 215, 255), (WIDTH // 2, HEIGHT // 2), radius, 1)
    draw_text(surface, word, FONT, WIDTH // 2, HEIGHT // 2 +150, 200, center = True)
    
# AURORA - appeards when all 12 constellations are in the sky

AURORA_GREEN = (120, 255, 190)
AURORA_VIOLET = (170, 120, 255)

def make_aurora_strip():
    strip = pygame.Surface((4, 220), pygame.SRCALPHA)
    for y in range(220):
        t = y / 220
        color = blend(AURORA_VIOLET, AURORA_GREEN, t)
        alpha = int(255 * t * t * (1 - t) * 6.75)
        pygame.draw.line(strip, with_alpha(color, min(255, alpha)), (0, y), (3, y))
    return strip

def draw_aurora(surface, strip, age):
    fade = min(1.0, age / 600)
    drift = age * 0.01
    for x in range(0, WIDTH, 4):
        wave = math.sin(x * 0.006 + drift) * 40 + math.sin(x * 0.013 - drift * 1.7) * 20
        shine = 0.5 + 0.5 * math.sin(x * 0.01 + drift * 2)
        strip.set_alpha(int(90 * fade * shine))
        surface.blit(strip, (x, 30 + wave))
    
    
# PLAYER, SHOOTING STARS AND EFFECTS

def make_player():
    return {"x": WIDTH / 2, "y": HEIGHT * 0.75, "pulse": 0.0, "trail": []}

def update_player(player):
    mouse_x, mouse_y = pygame.mouse.get_pos()
    
    # move quarter of the way to the mouse each frame -> soft, floating motion
    player["x"] += (mouse_x - player["x"]) * 0.25
    player["y"] += (mouse_y - player["y"]) * 0.25
    player["pulse"] += 0.05
    player["trail"].append((player["x"], player["y"]))
    if len(player["trail"]) > 12:
        player["trail"].pop(0)
        
def draw_player(surface, player):
    for i, point in enumerate(player["trail"]):
        draw_glow(surface, point[0], point[1], 6, (170, 200, 255), 8 + i * 4)
    size = 30 + int(math.sin(player["pulse"]) * 3)
    draw_glow(surface, player["x"], player["y"], size, (170, 200, 255), 90)
    draw_glow(surface, player["x"], player["y"], 9 , (235, 242, 255), 230)
        
def make_falling_star():
    speed = random.uniform(1.4, 4.6)        # some fall slowly, while some fall faster
    star = {
        "x": random.uniform(200, WIDTH - 200),
        "y": -20.0,
        "dx": random.uniform(-0.25, 0.25) * speed,          #diagonal angle
        "dy": speed,
        "color": random.choice(GLOW_COLORS),
        "trail": [],
        "caught": False,
        "landed": False,
        }
    return star

def update_falling_star(star):
    star["x"] += star['dx']
    star["y"] += star["dy"]
    star["trail"].append((star["x"], star["y"]))
    if len(star["trail"]) > TRAIL_LENGTH:
        star["trail"].pop(0)
        
def draw_star_tail(fx, star):
    "Thin tail that fades out and gets thinner with time"
    trail = star["trail"]
    for i in range(1, len(trail)):
        t = i / len(trail)      # small at end, 1 at head
        width = 1 if t < 0.6 else 2
        pygame.draw.line(fx, with_alpha(star["color"], int(170 * t)), trail[i - 1], trail[i], width)
        
def draw_star_head(surface, star):
    draw_glow(surface, star["x"], star["y"], 16, star["color"], 150)
    draw_glow(surface, star["x"], star["y"], 5, (255, 255, 255), 255)
    
def is_touching(player, star):
    distance = math.hypot(player["x"] - star["x"], player["y"] - star["y"])
    return distance < CATCH_RADIUS

def make_catch_effect(x, y, color, rings, particles):
    """Soft ring of light + glitter that floats away, lists are changed in place"""
    rings.append({"x": x, "y": y, "radius": 6.0, "life": 60, "color": color})
    for i in range(26):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(0.4, 2.6)
        life = random.randint(50, 110)
        particles.append({
            "x": x,
            "y": y,
            "dx": math.cos(angle) * speed,
            "dy": math.sin(angle) * speed,
            "life": life,
            "max_life": life,
            "color": random.choice(GLOW_COLORS),
            "size": random.choice([6, 8, 10]),
            "phase": random.uniform(0, math.pi * 2),
        })
        
def update_particle(p):
    p["x"] += p["dx"]
    p["y"] += p["dy"]
    p["dx"] *= 0.97                 #slowly loses speed
    p["dy"] *= 0.97
    p["dy"] -= 0.012                #float upwards
    p["phase"] += 0.3
    p["life"] -= 1
    
def draw_particles(surface, p):
    fade = p["life"] / p["max_life"]
    sparkle = 0.7 + 0.3 * math.sin(p["phase"])
    alpha = int(255 * fade * sparkle)
    draw_glow(surface, p["x"], p["y"], p["size"], p["color"], alpha)
    
def update_ring(ring):
    ring["radius"] += (70 - ring["radius"]) * 0.06      # grows faster, then slows down
    ring["life"] -= 1
    
def draw_ring(fx, ring):
    alpha = int(160 * ring["life"] / 60)
    center = (int(ring["x"]), int(ring["y"]))
    pygame.draw.circle(fx, with_alpha(ring["color"], alpha // 4), center, int(ring["radius"]) +3, 6)
    pygame.draw.circle(fx, with_alpha(ring["color"], alpha), center, int(ring["radius"]), 2)

    
def make_landing(x, color):
    return {"x": x, "life": 120, "color": color}

def draw_landing(surface, landing):
    """missed star leaves a soft glow that sinks into the horizon"""
    alpha = int(110 * landing["life"] / 120)
    draw_glow(surface, landing["x"], HEIGHT + 10, 60, landing["color"], alpha)
    
    
# ZODIAC CONSTELLATIONS

"""
Each constellation is directionary whose points are (x, y) tuples inside a
start index and end index are tuples that connect them

"""

CONSTELLATIONS = [
    {"name": "Pisces", "meaning": "the two fish",
     "points": [(0.85, 0.70), (0.95, 0.62), (0.93, 0.50), (0.82, 0.48), (0.75, 0.58),
                (0.60, 0.66), (0.42, 0.74), (0.22, 0.84), (0.05, 0.92), (0.10, 0.65),
                (0.15, 0.40), (0.12, 0.18), (0.22, 0.08), (0.25, 0.22)],
     "lines": [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (4, 5), (5, 6), (6, 7), (7, 8),
               (8, 9), (9, 10), (10, 11), (11, 12), (12, 13), (13, 10)]},
    {"name": "Aries", "meaning": "the ram",
     "points": [(0.10, 0.60), (0.55, 0.35), (0.75, 0.40), (0.85, 0.50)],
     "lines": [(0, 1), (1, 2), (2, 3)]},
    {"name": "Taurus", "meaning": "the bull",
     "points": [(0.55, 0.60), (0.45, 0.50), (0.35, 0.25), (0.62, 0.48), (0.85, 0.20),
                (0.75, 0.85), (0.90, 0.95)],
     "lines": [(0, 1), (1, 2), (0, 3), (3, 4), (0, 5), (5, 6)]},
    {"name": "Gemini", "meaning": "the twins",
     "points": [(0.20, 0.10), (0.30, 0.45), (0.38, 0.88), (0.45, 0.14), (0.56, 0.50),
                (0.72, 0.90), (0.10, 0.50), (0.75, 0.40)],
     "lines": [(0, 1), (1, 2), (3, 4), (4, 5), (0, 3), (1, 6), (4, 7)]},
    {"name": "Cancer", "meaning": "the crab",
     "points": [(0.50, 0.55), (0.48, 0.30), (0.45, 0.08), (0.20, 0.90), (0.82, 0.85)],
     "lines": [(0, 1), (1, 2), (0, 3), (0, 4)]},
    {"name": "Leo", "meaning": "the lion",
     "points": [(0.30, 0.75), (0.30, 0.55), (0.38, 0.38), (0.30, 0.20), (0.18, 0.12),
                (0.12, 0.25), (0.92, 0.60), (0.65, 0.45), (0.65, 0.68)],
     "lines": [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (2, 7), (7, 6), (6, 8), (8, 0)]},
    {"name": "Virgo", "meaning": "the maiden",
     "points": [(0.55, 0.95), (0.45, 0.65), (0.30, 0.50), (0.10, 0.45), (0.50, 0.40),
                (0.60, 0.15), (0.80, 0.30), (0.75, 0.60)],
     "lines": [(0, 1), (1, 2), (2, 3), (1, 4), (4, 5), (4, 6), (6, 7)]},
    {"name": "Libra", "meaning": "the scales",
     "points": [(0.50, 0.10), (0.20, 0.45), (0.80, 0.40), (0.30, 0.85), (0.75, 0.80)],
     "lines": [(0, 1), (0, 2), (1, 2), (1, 3), (2, 4)]},
    {"name": "Scorpius", "meaning": "the scorpion",
     "points": [(0.05, 0.15), (0.12, 0.30), (0.10, 0.45), (0.30, 0.40), (0.42, 0.50),
                (0.50, 0.68), (0.55, 0.85), (0.70, 0.92), (0.85, 0.85), (0.90, 0.70),
                (0.82, 0.60)],
     "lines": [(0, 1), (1, 2), (1, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10)]},
    {"name": "Sagittarius", "meaning": "the archer",
     "points": [(0.20, 0.50), (0.35, 0.35), (0.55, 0.30), (0.60, 0.50), (0.45, 0.60),
                (0.25, 0.75), (0.50, 0.80), (0.45, 0.10), (0.80, 0.40)],
     "lines": [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (0, 5), (5, 6), (6, 3), (1, 7),
               (7, 2), (3, 8)]},
    {"name": "Capricornus", "meaning": "the sea-goat",
     "points": [(0.10, 0.20), (0.20, 0.35), (0.45, 0.75), (0.60, 0.80), (0.85, 0.45),
                (0.95, 0.30), (0.60, 0.40)],
     "lines": [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 1)]},
    {"name": "Aquarius", "meaning": "the water-bearer",
     "points": [(0.15, 0.20), (0.30, 0.30), (0.50, 0.25), (0.60, 0.40), (0.55, 0.60),
                (0.70, 0.75), (0.85, 0.90), (0.40, 0.70), (0.30, 0.90)],
     "lines": [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (4, 7), (7, 8)]},
]

# Top-left corner (x, y) of the box where each constellation appears
SKY_SPOTS = [(80, 90), (380, 70), (650, 110), (130, 290), (430, 270), (720, 290), (980, 320), (60, 470), (340, 450), (630, 470), (920, 490), (820, 80)]
BOX_WIDTH = 210
BOX_HEIGHT = 150

def reveal_next_constellation(revealed, message):
    """Add the next zodiac sign to the sky, only if more left"""
    if len(revealed) < len(CONSTELLATIONS):
        index = len(revealed)
        revealed.append({"index": index, "age": 0})
        data = CONSTELLATIONS[index]
        show_message(message, f"{data['name']} has appeared in your sky - {data['meaning']}.", 300)

def draw_constellation(surface, entry, is_newest):
    data = CONSTELLATIONS[entry["index"]]
    left, top = SKY_SPOTS[entry["index"]]
    # convert 0..1 box positions into screen positions (list comprehension)
    points = [(left + p[0] * BOX_WIDTH, top + p[1] * BOX_HEIGHT) for p in data["points"]]
    progress = min(1.0, entry["age"] / REVEAL_FRAMES)

    if is_newest:
        line_color = (125, 140, 200)
    else:
        line_color = (80, 92, 140)               # older constellations stay softer

    # lines are drawn one after another, like someone tracing them
    total = len(data["lines"])
    for k in range(total):
        amount = progress * total - k            # how much of line k is drawn
        if amount <= 0:
            break
        amount = min(1.0, amount)
        a, b = data["lines"][k]
        start = points[a]
        end = points[b]
        end_now = (start[0] + (end[0] - start[0]) * amount,
                   start[1] + (end[1] - start[1]) * amount)
        pygame.draw.aaline(surface, line_color, start, end_now)

    # the stars of the constellation fade in
    star_alpha = int(220 * progress)
    for point in points:
        draw_glow(surface, point[0], point[1], 7, (225, 232, 255), star_alpha)

    # the name~ bright while new, then it stays as a faint label
    if entry["age"] < 480:
        label_alpha = int(220 * progress)
    else:
        label_alpha = max(70, 220 - (entry["age"] - 480))
    draw_text(surface, data["name"], SMALL_FONT, left + BOX_WIDTH // 2, top + BOX_HEIGHT + 14, label_alpha, center=True)


# Sunrise- the sky slowly brightens, and the stars fade away

DAWN_TOP = (92, 118, 178)
DAWN_MIDDLE = (214, 160, 170)
DAWN_HORIZON = (255, 190, 130)
SUN_COLOR = (255, 222, 170)
HILL_BACK = (150, 110, 140)
HILL_FRONT = (86, 68, 102)
BIRD_COLOR = (58, 46, 72)

def make_dawn_sky():
    """Gradient sky for sunrise- same as the night sky, but brighter"""
    dawn = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        t = y / HEIGHT
        if t < 0.6:
            color = blend(DAWN_TOP, DAWN_MIDDLE, t / 0.6)
        else:
            color = blend(DAWN_MIDDLE, DAWN_HORIZON, (t - 0.6) / 0.4)
        pygame.draw.line(dawn, color, (0, y), (WIDTH, y))
    return dawn

def make_hills(base_y, height, color):
    hills = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    shift = random.uniform(0, math.pi * 2)
    for x in range(WIDTH):
        wave = (math.sin(x * 0.004 + shift) * 0.6 + math.sin(x * 0.011 + shift * 2) * 0.3 + math.sin(x * 0.027) * 0.1)
        top = int(base_y - wave * height)
        pygame.draw.line(hills, color, (x, top), (x, HEIGHT))
    return hills

def make_dawn_cloud(y):
    width = random.randint(300, 520)
    height = random.randint(68, 100)
    image = make_cloud_image(width, height)
    image.fill((120, 70, 40, 0), special_flags = pygame.BLEND_RGBA_ADD)
    return {"image": image, "x": float(random.randint(-100, WIDTH - 380)), "y": y, "speed": random.uniform(0.1, 0.25)}

def make_birds():
    birds = []
    leader_x = -60
    leader_y = HEIGHT * 0.42
    for i in range(7):
        side = 1 if i % 2 == 0 else -1              # left or right wing of V
        row = (i + 1) // 2
        birds.append({
            "x": leader_x - row * 42,
            "y": leader_y + side * row * 24,
            "speed": 1.5,
            "phase": random.uniform(0, math.pi * 2),
            "size": random.choice([10, 11, 12]),
        })
    for x, y in [(-420, HEIGHT * 0.30), (-560, HEIGHT * 0.36)]:
        birds.append({"x": x, "y": y, "speed": 1.7, "phase": random.uniform(0, math.pi * 2), "size": 8})
    return birds

def make_dawn_scene():
    """keeping everything in a dictionary, so we can pass it around easily"""
    return {
        "sky": make_dawn_sky(),
        "hills_back": make_hills(HEIGHT - 150, 50, HILL_BACK),
        "hills_front": make_hills(HEIGHT - 70, 40, HILL_FRONT),
        "clouds": [make_dawn_cloud(y) for y in (60, 230, 300)],
        "birds": make_birds(),
    }
    
def update_dawn_scene(scene):
    for cloud in scene["clouds"]:
        cloud["x"] += cloud["speed"]
    for bird in scene ["birds"]:
        bird["x"] += bird["speed"]
        bird["y"] += math.sin(bird["phase"] * 0.3) * 0.15       # birds moving up and down slightly
        bird["phase"] += 0.18                                   # birds flapping wings
    
def draw_bird(surface, bird):
    """Bird is just two wings- 3 points joint by lines""" 
    flap = math.sin(bird["phase"]) * bird["size"] * 0.6
    x = bird["x"]
    y = bird["y"]
    size = bird["size"]
    points = [(x - size, y - flap), (x, y), (x + size, y - flap)]
    pygame.draw.lines(surface, BIRD_COLOR, False, points, 2)
    
def draw_sunrise(surface, scene, moon_disc, progress):
    """Progress goes upto 1 from 0- the sky warms up, the moon fades, the sun rises, and the birds fly"""
    smooth = progress * progress * (3 - 2 * progress)        # smoothstep
    
    scene["sky"].set_alpha(int(255 * smooth))
    surface.blit(scene["sky"], (0, 0))
    
    moon_disc.set_alpha(int(255 - 175 * smooth))
    surface.blit(moon_disc, (MOON_X - MOON_RADIUS, MOON_Y - MOON_RADIUS))
    moon_disc.set_alpha(255)
    
    sun_x = WIDTH // 2
    sun_y = HEIGHT + 60 - smooth * 330
    draw_glow(surface, sun_x, sun_y, 360, (255, 196, 148), int(110 * smooth))
    draw_glow(surface, sun_x, sun_y, 150, SUN_COLOR, int(190 * smooth))
    draw_glow(surface, sun_x, sun_y,  55, (255, 250, 236), int(255 * smooth))
    
    for cloud in scene["clouds"]:
        cloud["image"].set_alpha(int(150 * smooth))
        surface.blit(cloud["image"], (int(cloud["x"]), cloud["y"]))
        
    scene["hills_back"].set_alpha(int(255 * smooth))
    surface.blit(scene["hills_back"], (0, 0))
    scene["hills_front"].set_alpha(int(255 * smooth))
    surface.blit(scene["hills_front"], (0, 0))
    
    if progress > 0.3:
        for bird in scene["birds"]:
            draw_bird(surface, bird)
            
    if progress > 0.5:
        text_alpha = int(235 * (progress - 0.5) * 2)
        draw_text(surface, "The night is over, but the stars will always be in your heart.", TITLE_FONT, WIDTH // 2, 150, text_alpha, center = True)
        draw_text(surface, "A new day is waiting for you, with new ray of hope.", FONT, WIDTH // 2, 195, text_alpha, center = True)
        draw_text(surface, "And remember, you can always come back to wish upon a falling star.", FONT, WIDTH // 2, 220, text_alpha, center = True)


# Messages, Texts, and Music

def show_message(message, text, frames = 200):
    message["text"] = text
    message["timer"] = frames
    message["duration"] = frames

def draw_message(surface, message):
    if message["timer"] <= 0:
        return
                # fade in during first 30 frames, fade out during last 30
    shown = message["duration"] - message["timer"]
    fade = min(1.0, shown / 30, message["timer"] / 30)
    draw_text(surface, message["text"], FONT, WIDTH // 2, HEIGHT - 60, int(230 * fade), center = True)

def draw_hud(surface, caught, revealed_count, moon_label):
    draw_text(surface, "Moonlight Serenity", TITLE_FONT, 28, 20, 175)
    draw_text(surface, f"wishes caught: {caught}", SMALL_FONT, 30, 62, 150)
    draw_text(surface, f"constellations: {revealed_count} / {len(CONSTELLATIONS)}", SMALL_FONT, 30, 84, 150)
    draw_text(surface, "P: Pause     M: Music   B: Breathe    ESC: Leave", SMALL_FONT, WIDTH - 300, HEIGHT - 30, 100)
    draw_text(surface, moon_label, SMALL_FONT, MOON_X, MOON_Y + MOON_RADIUS + 22, 110, center = True)
    
def start_music():
    """Play music.mp3 on loop if exists. Return True if music is playing"""
    if not pygame.mixer.get_init():         # no sound available
        return False
    if not os.path.exists(MUSIC_PATH):
        return False
    pygame.mixer.music.load(MUSIC_PATH)
    pygame.mixer.music.set_volume(MUSIC_VOLUME)
    pygame.mixer.music.play(-1, fade_ms= 3000)      # if -1, loop forever, fade in over 3 seconds
    return True

def toggle_music(music_loaded, music_on):
    if not music_loaded:
        return False
    if music_on:
        pygame.mixer.music.pause()
    else:
        pygame.mixer.music.unpause()
    return not music_on

# MAIN GAME LOOP

def main():
    sky = make_sky()
    dawn_scene = make_dawn_scene()
    moon_phase = get_moon_phase()
    moon_disc = shade_moon(make_moon_disc(), moon_phase)
    moon_light = 0.25 + 0.75 * moon_brightness(moon_phase)
    moon_label = f"tonight: {phase_name(moon_phase)}"
    chimes = make_chimes()
    aurora = make_aurora_strip()
    twinkle_stars = make_twinkle_stars(90)
    clouds = [make_cloud() for i in range(4)]
    fx = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)           # layer for see through lines
    
    player = make_player()
    falling_stars = []
    particles = []
    rings = []
    landings = []
    revealed = []
    message = {"text": "", "timer": 0, "duration": 0}
    
    caught = 0
    spawn_timer = 0
    next_spawn = 40
    moon_pulse = 0.0
    paused = False
    ending = False                                                  # becomes true when sunrise starts
    end_timer = 0
    sound_on = True
    breathing = False
    breath_timer = 0
    aurora_age = 0
    music_loaded = start_music()
    music_on = music_loaded

    show_message(message, "Breatheee... and try to wish upon a falling star!", 300)
    
    running = True
    while running:
        clock.tick(FPS)
        
        # All inputs~
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                if ending:
                    running = False                                 # if pressed again- leave right away
                else:
                    ending = True                                   # start sunrise sequence
                    paused = False
                    if music_on:
                        pygame.mixer.music.fadeout(SUNRISE_FRAMES * 1000 // FPS)        # fade out music over the sunrise
            elif event.type == pygame.KEYDOWN and not ending:
                if event.key == pygame.K_p:
                    paused = not paused
                elif event.key == pygame.K_m:
                    sound_on = not sound_on
                    music_on = toggle_music(music_loaded, music_on)
                elif event.key == pygame.K_b:
                    breathing = not breathing
                    breath_timer = 0
                    
                    
        #  All updates~
        if not paused:
            spawn_timer += 1
            if spawn_timer >= next_spawn and not ending:
                falling_stars.append(make_falling_star())
                spawn_timer = 0
                next_spawn = random.randint(35, 80)
                
            update_player(player)
            update_twinkle_stars(twinkle_stars)
            moon_pulse += 0.01
            for cloud in clouds:
                update_cloud(cloud)
                
            for star in falling_stars:
                update_falling_star(star)
                if star["landed"]:
                    continue
                if is_touching(player, star):
                    star["caught"] = True
                    caught += 1
                    make_catch_effect(star["x"], star["y"], star["color"], rings, particles)
                    if chimes and sound_on:
                        random.choice(chimes).play()
                    if caught % STARS_PER_CONSTELLATION == 0:
                        reveal_next_constellation(revealed, message)
                elif star["y"] > HEIGHT:
                    star["landed"] = True
                    landings.append(make_landing(star["x"], star["color"]))
                    if message["timer"] == 0 and random.random() < 0.35:
                        show_message(message, random.choice(MISS_MESSAGES))
                    
            # keeping only stars with visible tail and stars that are not caught yet
            falling_stars = [s for s in falling_stars if not s["caught"] and s["trail"][0][1] < HEIGHT + 5]
                    
            for p in particles:
                update_particle(p)
            particles = [p for p in particles if p["life"] > 0]
                    
            for ring in rings:
                update_ring(ring)
            rings = [r for r in rings if r["life"] > 0]
                    
            for landing in landings:
                landing["life"] -= 1
            landings = [landing for landing in landings if landing["life"] > 0]
                    
            for entry in revealed:
                entry["age"] += 1
            if message["timer"] > 0:
                message["timer"] -= 1
            if breathing:
                breath_timer += 1
                
            if len(revealed) == len(CONSTELLATIONS):
                aurora_age +=1
                if aurora_age == 360:
                    show_message(message, "All 12 signs are with you now... and the sky is shining only for you.", 360)
                
        if ending:
            end_timer += 1
            update_dawn_scene(dawn_scene)
            if end_timer >= SUNRISE_FRAMES + 180:
                running = False
                        
                        
        # Draw~ Back to front
                
        screen.blit(sky, (0, 0))
        if aurora_age > 0:
            draw_aurora(screen, aurora, aurora_age)
            
        draw_twinkle_stars(screen, twinkle_stars)
        for entry in revealed:
            draw_constellation(screen, entry, entry["index"] == len(revealed) - 1)
        draw_moon(screen, moon_disc, moon_pulse, moon_light)
        for cloud in clouds:
                draw_cloud(screen, cloud)
        for landing in landings:
                draw_landing(screen, landing)
                    
        fx.fill((0, 0, 0, 0))                   # clear the see through layer
                    
        for star in falling_stars:
            draw_star_tail(fx, star)
        for ring in rings:
            draw_ring(fx, ring)
        screen.blit(fx, (0, 0))
                    
        for star in falling_stars:
            draw_star_head(screen, star)
        for p in particles:
            draw_particles(screen, p)
        draw_player(screen, player)
        
        if ending:
            draw_sunrise(screen, dawn_scene, moon_disc, min(1.0, end_timer / SUNRISE_FRAMES))
        else:
            if breathing:
                draw_breathing(screen, breath_timer)
            draw_hud(screen, caught, len(revealed), moon_label)
            draw_message(screen, message)
                    
        if paused:
            shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            shade.fill((0, 0, 10, 120))
            screen.blit(shade, (0, 0))
            draw_text(screen, "paused", TITLE_FONT, WIDTH // 2, HEIGHT // 2 - 20, center = True)
            draw_text(screen, "the sky will always wait for you~ press P", FONT, WIDTH // 2, HEIGHT // 2 + 25, 210, center = True)
                    
                    
    
        pygame.display.flip()

    pygame.quit()

main()