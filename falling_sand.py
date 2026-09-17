import colorsys
import random
import sys

import pygame

# Window Size
WINDOW_WIDTH: int = 1280
WINDOW_HEIGHT: int = 720
# SIZE OF PARTICLE
CELL_SIZE: int = 6

BACKGROUND_COLOR = (45, 45, 45)


class Grid:
    def __init__(self, width: int, height: int, cell_size: int):
        self.cell_size = cell_size
        self.rows = height // cell_size
        self.columns = width // cell_size
        self.cells: list[list[Particle | None]] = [
            [None for _ in range(self.columns)] for _ in range(self.rows)
        ]

    def draw(self, window: pygame.Surface):
        for row in range(self.rows):
            for column in range(self.columns):
                particle = self.cells[row][column]
                if particle is not None:
                    pygame.draw.rect(
                        window,
                        particle.color,
                        (
                            column * self.cell_size,
                            row * self.cell_size,
                            self.cell_size,
                            self.cell_size,
                        ),
                    )

    def add_particle(self, row: int, column: int, particle_type):
        if (
            0 <= row < self.rows
            and 0 <= column < self.columns
            and self.is_cell_empty(row, column)
        ):
            self.cells[row][column] = particle_type

    def remove_particle(self, row: int, column: int):
        if 0 <= row < self.rows and 0 <= column < self.columns:
            self.cells[row][column] = None

    def is_cell_empty(self, row: int, column: int) -> bool:
        if not (0 <= row < self.rows and 0 <= column < self.columns):
            return False

        return self.cells[row][column] is None

    def is_cell_permeable(self, row: int, column: int) -> bool:
        cell = self.get_cell(row, column)
        return cell is not None and cell.permeable

    def move_particle(
        self, row: int, column: int, new_row: int, new_column: int
    ) -> bool:
        if (row, column) == (new_row, new_column):
            return False

        if not (
            0 <= row < self.rows
            and 0 <= column < self.columns
            and 0 <= new_row < self.rows
            and 0 <= new_column < self.columns
        ):
            return False

        particle = self.cells[row][column]
        destination = self.cells[new_row][new_column]
        if particle is None:
            return False
        if particle.fixed or (destination is not None and destination.fixed):
            return False
        if destination is not None:
            if particle.permeable:
                return False
            if destination.permeable and new_row == row + 1 and new_column == column:
                self.cells[row][column], self.cells[new_row][new_column] = (
                    destination,
                    particle,
                )
                return True
            if not self.push_up(new_row, new_column):
                return False

        self.cells[new_row][new_column] = particle
        self.cells[row][column] = None
        return True

    def push_up(self, row: int, column: int) -> bool:
        if row == 0:
            return False
        above = self.cells[row - 1][column]
        if above is not None and (
            not above.permeable or not self.push_up(row - 1, column)
        ):
            return False
        self.cells[row - 1][column] = self.cells[row][column]
        self.cells[row][column] = None
        return True

    def set_cell(self, row: int, column: int, particle):
        if 0 <= row < self.rows and 0 <= column < self.columns:
            self.cells[row][column] = particle

    def get_cell(self, row: int, column: int):
        if 0 <= row < self.rows and 0 <= column < self.columns:
            return self.cells[row][column]
        return None

    def clear(self):
        for row in range(self.rows):
            for column in range(self.columns):
                self.cells[row][column] = None


class Particle:
    """Parent particle class"""

    def __init__(self) -> None:
        self.permeable = False
        self.fixed = False

    color: tuple[int, int, int]

    def random_color(
        self,
        hue_range: tuple[float, float],
        saturation_range: tuple[float, float],
        value_range: tuple[float, float],
    ):
        """Randomize color within hsv range"""
        hue = random.uniform(*hue_range)
        saturation = random.uniform(*saturation_range)
        value = random.uniform(*value_range)
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        return (int(r * 255), int(g * 255), int(b * 255))


class SandParticle(Particle):
    """Sand Particle behavior"""

    def __init__(self) -> None:
        super().__init__()
        self.color = self.random_color((0.1, 0.12), (0.5, 0.7), (0.7, 0.9))

    def update(self, grid: Grid, row: int, column: int) -> tuple[int, int]:
        # check if cell below is empty
        below = grid.get_cell(row + 1, column)
        if below is None or grid.is_cell_permeable(row + 1, column):
            return row + 1, column
        else:
            # randomize left or right
            offsets = [-1, 1]
            random.shuffle(offsets)
            # place left or right
            for offset in offsets:
                new_column = column + offset
                diagonal = grid.get_cell(row + 1, new_column)
                if diagonal is None or grid.is_cell_permeable(row + 1, new_column):
                    return (row + 1, new_column)
        return row, column


class RockParticle(Particle):
    """Rock Behavior

    Args:
        Particle (class): Parent Class
    """

    def __init__(self) -> None:
        super().__init__()
        self.color = self.random_color((0.0, 0.1), (0.1, 0.3), (0.3, 0.5))
        self.fixed = True


class WaterParticle(Particle):
    """Water Behavior

    Args:
        Particle (class): Parent Class
    """

    def __init__(self):
        super().__init__()
        self.color = self.random_color((0.58, 0.63), (0.65, 0.78), (0.85, 0.95))
        self.permeable = True

    def update(self, grid: Grid, row: int, column: int) -> tuple[int, int]:
        """if it can move down, it moves down, else move left or right.

        Args:
            grid (Grid): game grid
            row (int): current y
            column (int): current x pos

        Returns:
            tuple[int, int]: New Water Particle Position
        """
        if grid.is_cell_empty(row + 1, column):
            return row + 1, column

        offsets = [-1, 1]
        random.shuffle(offsets)
        for offset in offsets:
            if grid.is_cell_empty(row + 1, column + offset):
                return row + 1, column + offset

        for offset in offsets:
            if grid.is_cell_empty(row, column + offset):
                return row, column + offset

        return row, column


class Mode:
    """Brush Modes"""

    ERASE = 0
    SAND = 1
    ROCK = 2
    WATER = 3


class Simulation:
    """Creates and manages Grid, Adds and Removes Particles, Coordinates overall Simulation"""

    def __init__(self):
        self.grid = Grid(WINDOW_WIDTH, WINDOW_HEIGHT, CELL_SIZE)
        self.mode = Mode.SAND
        self.brush_size = 3
        self.sand_brush_volume = 0.15
        self.font = pygame.font.Font(None, 24)
        self.fps = 120

    def draw(self, window: pygame.Surface):
        self.grid.draw(window)
        self.draw_brush(window)
        self.draw_hud(window)

    def draw_hud(self, window: pygame.Surface):
        lines = [
            f"Mode: {self.mode}",
            f"Brush size: {self.brush_size}",
            f"Sand volume: {self.sand_brush_volume:.0%}",
            f"Game Speed: {self.fps}",
            "",
            "Controls:",
            "1/2: Game Speed",
            "S: Sand   R: Rock   E: Erase   W: Water",
            "Up/Down: Brush Size",
            "Left/Right: Sand Volume",
            "Left mouse: Draw or Erase",
            "Space: Clear Grid",
        ]
        line_height = self.font.get_linesize()

        # Adjust these to position text
        start_x = 15
        start_y = 15

        for line_number, line in enumerate(lines):
            # Skip empty lines to save performance
            if line.strip() == "":
                continue

            text = self.font.render(line, True, (235, 235, 235))
            window.blit(
                text,
                (start_x, start_y + line_number * line_height),
            )

    def add_particle(self, row: int, column: int):
        if self.mode == Mode.SAND:
            if random.random() < self.sand_brush_volume:
                self.grid.add_particle(row, column, SandParticle())
        elif self.mode == Mode.ROCK:
            self.grid.add_particle(row, column, RockParticle())
        elif self.mode == Mode.WATER:
            self.grid.add_particle(row, column, WaterParticle())

    def remove_particle(self, row: int, column: int):
        self.grid.remove_particle(row, column)

    def update(self):
        movable_particles = (SandParticle, WaterParticle)
        positions_by_row: dict[int, list[int]] = {}
        for row in range(self.grid.rows):
            for column in range(self.grid.columns):
                particle = self.grid.get_cell(row, column)
                if isinstance(particle, movable_particles):
                    positions_by_row.setdefault(row, []).append(column)

        # starts from bottom
        for row in sorted(positions_by_row, reverse=True):
            columns = positions_by_row[row]
            columns.sort(reverse=(row % 2 != 0))
            for column in columns:
                particle = self.grid.get_cell(row, column)
                if not isinstance(particle, movable_particles):
                    continue
                new_pos = particle.update(self.grid, row, column)
                if new_pos != (row, column):
                    self.grid.move_particle(row, column, new_pos[0], new_pos[1])

    def restart(self):
        self.grid.clear()

    def handle_controls(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                self.handle_key(event)
        self.handle_mouse()

    def handle_key(self, event: pygame.event.Event):
        if event.key == pygame.K_SPACE:
            # Reset simulation
            self.restart()
        elif event.key == pygame.K_s:
            print("Sand Mode")
            self.mode = Mode.SAND
        elif event.key == pygame.K_r:
            print("Rock Mode")
            self.mode = Mode.ROCK
        elif event.key == pygame.K_e:
            print("Eraser Mode")
            self.mode = Mode.ERASE
        elif event.key == pygame.K_w:
            self.mode = Mode.WATER
        elif event.key == pygame.K_UP:
            self.brush_size += 1
        elif event.key == pygame.K_DOWN and self.brush_size >= 2:
            self.brush_size -= 1
        elif event.key == pygame.K_RIGHT and self.sand_brush_volume < 1.0:
            self.sand_brush_volume += 0.01
        elif event.key == pygame.K_LEFT and self.sand_brush_volume > 0.01:
            self.sand_brush_volume -= 0.01
        elif event.key == pygame.K_2 and self.fps < 300:
            self.fps += 10
        elif event.key == pygame.K_1 and self.fps > 10:
            self.fps -= 10

    def handle_mouse(self):
        buttons = pygame.mouse.get_pressed()
        if buttons[0]:
            pos = pygame.mouse.get_pos()
            row = pos[1] // CELL_SIZE
            column = pos[0] // CELL_SIZE

            self.apply_brush(row, column)

    def apply_brush(self, row: int, column: int):
        half = self.brush_size // 2
        for r in range(-half, self.brush_size - half):
            for c in range(-half, self.brush_size - half):
                current_row = row + r
                current_column = column + c

                if self.mode == Mode.ERASE:
                    self.grid.remove_particle(current_row, current_column)
                else:
                    self.add_particle(current_row, current_column)

    def draw_brush(self, window: pygame.Surface):
        mouse_pos = pygame.mouse.get_pos()
        column = mouse_pos[0] // CELL_SIZE
        row = mouse_pos[1] // CELL_SIZE
        half = self.brush_size // 2

        brush_visual_size = self.brush_size * CELL_SIZE
        color = (255, 255, 255)

        if self.mode == Mode.ROCK:
            color = (100, 100, 100)
        elif self.mode == Mode.SAND:
            color = (185, 142, 66)
        elif self.mode == Mode.ERASE:
            color = (255, 55, 55)
        elif self.mode == Mode.WATER:
            color = (0, 0, 255)

        pygame.draw.rect(
            window,
            color,
            (
                (column - half) * CELL_SIZE,
                (row - half) * CELL_SIZE,
                brush_visual_size,
                brush_visual_size,
            ),
        )


def init_game():
    global window, clock, simulation
    pygame.init()
    pygame.mouse.set_visible(False)
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Falling Sand")

    clock = pygame.time.Clock()
    simulation = Simulation()


def main():
    # Simulation loop
    running = True
    while running:
        # Event Handling
        simulation.handle_controls()

        # Update State
        simulation.update()

        # Drawing
        window.fill(BACKGROUND_COLOR)
        simulation.draw(window)

        pygame.display.flip()
        clock.tick(simulation.fps)


if __name__ == "__main__":
    init_game()
    main()
