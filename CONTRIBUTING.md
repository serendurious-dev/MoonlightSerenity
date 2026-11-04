# Contributing

Thank you for wanting to add to the sky. 🌙

## The one rule

**Nothing should add pressure.** No penalties, timers, failure states, lives or scores that go down. If an idea makes the game more stressful, it doesn't belong here, however fun it is.

Ideas that fit well are calmer visuals, gentler sounds, more kindness and small personal touches.

## How to contribute

1. Fork the repository and create a branch: `git checkout -b my-idea`
2. Keep the existing style: each object is a dictionary, with `make_` / `update_` / `draw_` functions and constants in `UPPER_CASE` at the top of their section.
3. Run the game and check that it still holds a steady 60 FPS.
4. Open a pull request that describes what you changed and how it feels to play.

## Reporting a problem

Open an issue with:
- what you expected, and what happened instead
- your OS, Python version and pygame version (`python -m pygame.version`)
- the error message, if there was one
