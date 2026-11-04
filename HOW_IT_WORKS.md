# How Moonlight Serenity works

This walks through the whole game, one system at a time.

## The big picture

The game is one file and one loop. Everything in the world is a **dictionary**, and objects of the same kind are kept in a **list**:

```python
star = {"x": 640.0, "y": -20.0, "dx": 0.3, "dy": 2.1, "color": (170, 210, 255),
        "trail": [], "caught": False, "landed": False}
falling_stars = [star, ...]
```

Each kind of object gets three small functions:

| Function | Job |
|---|---|
| `make_thing()` | builds and returns a new dictionary |
| `update_thing(thing)` | moves it by one frame |
| `draw_thing(surface, thing)` | paints it |

`main()` runs this loop 60 times per second (`clock.tick(FPS)`):

1. **Input:** read keyboard and window events (P, M, B, Esc).
2. **Update:** spawn stars, move everything, check catches, then remove finished things with list comprehensions.
3. **Draw, back to front:** sky → aurora → twinkling stars → constellations → moon → clouds → tails and rings → stars → particles → player → HUD and messages → sunrise (when leaving) → `pygame.display.flip()`.

One frame is 1/60 of a second, so all timings are counted in frames. For example, `REVEAL_FRAMES = 240` is 4 seconds.

## Drawing light: the glow cache

Almost everything that shines is a **soft glow**: many circles drawn from the edge inward, with transparency rising as `strength ** 2`. That's slow to build, so each glow is built once and stored:

```python
glow_cache = {}                 # key: (radius, color) tuple → value: glow image
```

Tuples can be dictionary keys because they're **immutable**, and therefore hashable. After the first frame, drawing a glow is just one fast `blit`.

Surfaces made with `pygame.SRCALPHA` keep a transparency value for every pixel. That's what lets glows fade smoothly into the sky. `with_alpha(color, a)` turns `(r, g, b)` into `(r, g, b, a)` using tuple concatenation: `color + (a,)`.

## The sky (built once)

- **Gradient:** each row's color is `blend()`-ed between three colors, `SKY_TOP` → `SKY_MIDDLE` → `SKY_HORIZON`.
- **Milky Way:** faint haze glows and 1,600 tiny stars scattered along a diagonal band with `random.gauss`.
- **Dim stars:** `random.random() ** 1.3` pushes more stars toward the top, like a real sky.

The finished image is reused every frame. Only the **twinkling stars** change: each has a `phase` that grows slowly, and its brightness follows `math.sin(phase)`.

## Catching stars

- The wisp moves **a quarter of the way** to the mouse each frame, which makes it float softly.
- A star is caught when `math.hypot(dx, dy) < CATCH_RADIUS`, which is the distance between the two centers.
- A catch creates one expanding **ring** and 26 **particles** that drift outward, slow down (`*= 0.97`) and float upward.
- A missed star sets `landed = True` and leaves a fading glow at the horizon. That's all that happens.

## Constellations

Each sign is a dictionary of **points**, as fractions from 0 to 1 inside a 210×150 box, and **lines**, as pairs of point indexes. A list comprehension turns the fractions into screen pixels. While a sign is new, `progress` grows from 0 to 1, and line *k* is drawn by the amount `progress * total - k`, so the lines trace themselves one after another.

## Chimes (v1.2)

Each note is generated in code:

```python
wave = sin(2π · f · t) + 0.3 · sin(2π · 2f · t)    # tone plus a softer octave → music-box
fade = exp(-3.2 · t)                                # rings, then fades
```

The samples are stored in an `array("h")` of 16-bit integers and handed to `pygame.mixer.Sound`. The six notes, C D E G A C, form a **pentatonic scale**, so random notes always sound gentle together.

## Real moon phase (v1.2)

```python
days  = (now - KNOWN_NEW_MOON).total_seconds() / 86400
phase = (days % 29.530588853) / 29.530588853        # 0 = new, 0.5 = full
```

The moon is shaded **row by row**. On each row, `half = √(R² − y²)` is the half-width, and `half · cos(2π · phase)` is where light meets shadow. The dark side gets a see-through navy, so a faint "earthshine" stays visible. A thin crescent's halo glows less.

## Breathing guide (v1.2)

`timer % 600` repeats every 10 seconds: 240 frames growing (breathe in), then 360 shrinking (breathe out). The smoothstep curve `t² (3 − 2t)` makes the circle start and stop gently. A longer breath out is what calms the body.

## Aurora (v1.2)

One thin strip of light is pre-drawn, violet at the top and green near the bottom. Each frame it's drawn every 4 pixels across the screen. Each copy is moved up and down by two sine waves and brightened by a third. All three depend on a slowly growing `drift`, so the curtain sways.

## Sunrise (v1.1)

Pressing Esc doesn't quit. It sets `ending = True` and starts `end_timer`. Over `SUNRISE_FRAMES` (8 s):

- the dawn gradient fades in over the night with `set_alpha`
- the sun (three layered glows) rises from behind the hills
- the hills are drawn column by column, with each column's height a **sum of three sine waves**
- birds are 3 points joined by lines, with wing tips that flap by `sin(phase)`
- the closing words fade in

The game closes 3 seconds after the sun is up, or right away if Esc is pressed again.

## Tweaking

| Constant | Effect |
|---|---|
| `CATCH_RADIUS` | bigger = easier to catch |
| `STARS_PER_CONSTELLATION` | wishes needed per sign |
| `REVEAL_FRAMES` | how slowly a sign draws itself |
| `SUNRISE_FRAMES` | length of the sunrise |
| `MUSIC_VOLUME`, `CHIME_VOLUME` | loudness |
| `BREATHE_IN`, `BREATHE_OUT` | breathing rhythm (in frames) |
| `MISS_MESSAGES` | the kind words the sky says |
