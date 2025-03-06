import pygame
import sys
import random
import math
import time

# Constants
WIDTH, HEIGHT = 600, 480
ROWS, COLS = 20, 25
CELL_SIZE = WIDTH // COLS

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
PINK = (255, 100, 150)
BLUE = (0, 0, 255)
RED = (255, 0, 0)

# Directions
DIRECTIONS = [(0, 1), (1, 0), (0, -1), (-1, 0)]


class Maze:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = self._generate_maze()

    def _generate_maze(self):
        """Generate a maze using Depth-First Search."""
        maze = [[1 for _ in range(self.cols)] for _ in range(self.rows)]
        start_row, start_col = random.randint(0, self.rows - 1), random.randint(0, self.cols - 1)
        maze[start_row][start_col] = 0

        stack = [(start_row, start_col)]
        while stack:
            current_row, current_col = stack[-1]
            neighbors = [
                (current_row + 2 * dr, current_col + 2 * dc)
                for dr, dc in DIRECTIONS
                if 0 <= current_row + 2 * dr < self.rows
                and 0 <= current_col + 2 * dc < self.cols
                and maze[current_row + 2 * dr][current_col + 2 * dc] == 1
            ]

            if neighbors:
                next_row, next_col = random.choice(neighbors)
                maze[next_row][next_col] = 0
                maze[current_row + (next_row - current_row) // 2][current_col + (next_col - current_col) // 2] = 0
                stack.append((next_row, next_col))
            else:
                stack.pop()

        return maze

    def place_characters(self):
        """Place Pac-Man and Ghost in random open cells."""
        open_cells = [(r, c) for r in range(self.rows) for c in range(self.cols) if self.grid[r][c] == 0]
        pacman_pos = random.choice(open_cells)
        ghost_pos = random.choice([cell for cell in open_cells if cell != pacman_pos])
        return pacman_pos, ghost_pos

    def generate_dots(self):
        """Generate dots in open cells."""
        return {(r, c) for r in range(self.rows) for c in range(self.cols) if self.grid[r][c] == 0}

    def draw(self, screen, dots):
        """Draw the maze and dots."""
        for i in range(self.rows):
            for j in range(self.cols):
                if self.grid[i][j] == 1:
                    pygame.draw.rect(screen, BLUE, (j * CELL_SIZE, i * CELL_SIZE, CELL_SIZE, CELL_SIZE))

        for dot in dots:
            pygame.draw.circle(screen, WHITE, (dot[1] * CELL_SIZE + CELL_SIZE // 2, dot[0] * CELL_SIZE + CELL_SIZE // 2), 2)


class Pacman:
    def __init__(self, pos):
        self.pos = pos
        self.mouth_angle = 30
        self.mouth_direction = 1

    def draw(self, screen):
        """Draw Pac-Man."""
        x, y = self.pos
        pacman_radius = CELL_SIZE // 2 - 2
        pacman_x = y * CELL_SIZE + CELL_SIZE // 2
        pacman_y = x * CELL_SIZE + CELL_SIZE // 2

        pygame.draw.arc(screen, YELLOW, (pacman_x - pacman_radius, pacman_y - pacman_radius, pacman_radius * 2, pacman_radius * 2),
                        math.radians(self.mouth_angle), math.radians(360 - self.mouth_angle), pacman_radius)
        pygame.draw.circle(screen, BLACK, (pacman_x + pacman_radius // 3, pacman_y - pacman_radius // 3), 3)

    def update(self):
        """Update Pac-Man's mouth animation."""
        self.mouth_angle += 5 * self.mouth_direction
        if self.mouth_angle >= 45 or self.mouth_angle <= 0:
            self.mouth_direction *= -1


class Ghost:
    def __init__(self, pos):
        self.pos = pos

    def draw(self, screen, target_pos):
        """Draw the ghost."""
        x, y = self.pos
        ghost_radius = CELL_SIZE // 2 - 2
        ghost_x = y * CELL_SIZE + CELL_SIZE // 2
        ghost_y = x * CELL_SIZE + CELL_SIZE // 2

        pygame.draw.circle(screen, PINK, (ghost_x, ghost_y - ghost_radius // 3), ghost_radius)
        pygame.draw.rect(screen, PINK, (ghost_x - ghost_radius, ghost_y - ghost_radius // 3, ghost_radius * 2, ghost_radius))

        eye_offset_x = ghost_radius // 3
        eye_offset_y = ghost_radius // 4
        pupil_max_offset = ghost_radius // 8

        direction_x = target_pos[1] - self.pos[1]
        direction_y = target_pos[0] - self.pos[0]
        magnitude = max(abs(direction_x), abs(direction_y), 1)

        pupil_offset_x = (direction_x / magnitude) * pupil_max_offset
        pupil_offset_y = (direction_y / magnitude) * pupil_max_offset

        pygame.draw.circle(screen, WHITE, (ghost_x - eye_offset_x, ghost_y - eye_offset_y), ghost_radius // 4)
        pygame.draw.circle(screen, WHITE, (ghost_x + eye_offset_x, ghost_y - eye_offset_y), ghost_radius // 4)

        pygame.draw.circle(screen, BLACK, (int(ghost_x - eye_offset_x + pupil_offset_x), int(ghost_y - eye_offset_y + pupil_offset_y)), ghost_radius // 8)
        pygame.draw.circle(screen, BLACK, (int(ghost_x + eye_offset_x + pupil_offset_x), int(ghost_y - eye_offset_y + pupil_offset_y)), ghost_radius // 8)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pac-Man DFS Ghost")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.maze = Maze(ROWS, COLS)
        self.pacman_pos, self.ghost_pos = self.maze.place_characters()
        self.dots = self.maze.generate_dots()
        self.pacman = Pacman(self.pacman_pos)
        self.ghost = Ghost(self.ghost_pos)
        self.path = []
        self.game_over = False

    def dfs(self, start, goal):
        """Perform Depth-First Search to find a path from start to goal."""
        start_time = time.time()
        stack = [(start, [start])]
        visited = set()
        expanded_nodes = 0
        max_memory_usage = 0

        while stack:
            current_memory = sys.getsizeof(stack) + sys.getsizeof(visited)
            max_memory_usage = max(max_memory_usage, current_memory)

            (current, current_path) = stack.pop()
            expanded_nodes += 1

            if current == goal:
                search_time = time.time() - start_time
                return current_path, search_time, max_memory_usage, expanded_nodes

            if current in visited:
                continue

            visited.add(current)

            for dr, dc in DIRECTIONS:
                next_pos = (current[0] + dr, current[1] + dc)
                if 0 <= next_pos[0] < self.maze.rows and 0 <= next_pos[1] < self.maze.cols and self.maze.grid[next_pos[0]][next_pos[1]] != 1:
                    stack.append((next_pos, current_path + [next_pos]))

        search_time = time.time() - start_time
        return None, search_time, max_memory_usage, expanded_nodes

    def run(self):
        """Run the game loop."""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            if not self.game_over:
                if not self.path:
                    self.path, search_time, memory_usage, expanded_nodes = self.dfs(self.ghost.pos, self.pacman.pos)
                    print(f"Search Time: {search_time:.6f} seconds")
                    print(f"Max Memory Usage: {memory_usage} bytes")
                    print(f"Expanded Nodes: {expanded_nodes}")

                if self.path and len(self.path) > 1:
                    self.ghost.pos = self.path.pop(0)

                if len(self.path) == 1 and self.path[0] == self.pacman.pos:
                    self.ghost.pos = self.pacman.pos

                if self.ghost.pos == self.pacman.pos:
                    self.game_over = True

                self.pacman.update()

            self.screen.fill(BLACK)
            self.maze.draw(self.screen, self.dots)
            self.pacman.draw(self.screen)
            self.ghost.draw(self.screen, self.pacman.pos)

            if self.game_over:
                game_over_text = self.font.render("GAME OVER!", True, RED)
                self.screen.blit(game_over_text, (WIDTH // 2 - 80, HEIGHT // 2 - 20))
                pygame.display.flip()
                pygame.time.delay(300)
                break

            pygame.display.flip()
            self.clock.tick(7)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()