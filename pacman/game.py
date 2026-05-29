import pygame
from pacman.engine import PacmanEngine
from pacman.render.renderer import GameRenderer, FPS


class Game:
    """Coordinates core execution mechanics and rendering cycles.

    Attributes:
        engine: Core simulation processing backend connection.
        renderer: Active graphical context surface pipeline interface.
        clock: High resolution tracking scheduler for hardware ticks.
        running: Control condition managing active loop lifetimes.
    """

    def __init__(self, engine: PacmanEngine) -> None:
        """Initializes game execution wrappers with logic bindings.

        Args:
            engine: Shared reference to the central backend logic driver.
        """
        pygame.init()
        self.engine: PacmanEngine = engine
        self.renderer: GameRenderer = GameRenderer(engine)
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.running: bool = False

    def _handle_events(self) -> None:
        """Intercepts hardware interactions and schedules updates."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    self.engine.pac_next_dir = 'E'
                    self.engine.pac_next_dir_timer = 0.0
                elif event.key == pygame.K_LEFT:
                    self.engine.pac_next_dir = 'W'
                    self.engine.pac_next_dir_timer = 0.0
                elif event.key == pygame.K_UP:
                    self.engine.pac_next_dir = 'N'
                    self.engine.pac_next_dir_timer = 0.0
                elif event.key == pygame.K_DOWN:
                    self.engine.pac_next_dir = 'S'
                    self.engine.pac_next_dir_timer = 0.0
                elif event.key == pygame.K_ESCAPE:
                    self.running = False

    def run(self) -> None:
        """Launches the primary block runtime simulation container."""
        self.running = True

        while self.running:
            dt: float = self.clock.tick(FPS) / 1000.0
            self._handle_events()
            self.engine.update(dt)
            self.renderer.draw_grid()
            self.renderer.draw_pacman()
            pygame.display.flip()

        pygame.quit()
