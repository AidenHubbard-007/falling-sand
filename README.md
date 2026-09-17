# Falling Sand Simulation

A falling-sand simulation built with Python and Pygame.

## Requirements

- Python 3.10 or newer
- Pygame-ce

## Setup

Install Pygame-ce:

```bash
python -m pip install pygame-ce
```

Run the simulation:

```bash
python falling_sand.py
```

## Controls

| Key or input      | Action                           |
| ----------------- | -------------------------------- |
| `S`               | Select sand mode                 |
| `R`               | Select rock mode                 |
| `E`               | Select erase mode                |
| Up / Down         | Increase or decrease brush size  |
| Left / Right      | Decrease or increase sand volume |
| `1` / `2`         | Decrease or increase game speed  |
| Left mouse button | Draw or erase particles          |
| Space             | Clear the grid                   |

## Particle behavior

- **Sand** falls downward and moves diagonally when the space below is blocked.
- **Rock** stays in place and can be used as a solid obstacle.
- **Erase** removes particles from the grid.
