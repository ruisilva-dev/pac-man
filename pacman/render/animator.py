class Animator:
    """A generic frame pacing utility for sprite animations.

    Accumulates delta time and advances a frame index based on a target
    frames-per-second rate. Includes optional pausing between cycles.

    Attributes:
        fps: Target speed of the animation in frames per second.
        frame_count: Total number of frames in the animation loop.
        wait_interval: Optional pause duration in seconds after a full loop.
        current_frame: The current active index of the animation.
    """

    def __init__(
        self, fps: float, frame_count: int, wait_interval: float = 0.0
    ) -> None:
        """Initializes the animator with its timing constraints.

        Args:
            fps: Target playback speed in frames per second.
            frame_count: Total number of visual frames in the sequence.
            wait_interval: Optional delay in seconds before repeating.
        """
        self.fps: float = fps
        self.frame_count: int = frame_count
        self.wait_interval: float = wait_interval

        self.current_frame: int = 0
        self._timer: float = 0.0
        self._wait_timer: float = 0.0

    def update(self, dt: float) -> bool:
        """Advances the animation timing, cycling frames when appropriate.

        Args:
            dt: Delta time in seconds since the last frame.

        Returns:
            True if the animation just completed a full loop cycle.
        """
        if self._wait_timer > 0.0:
            self._wait_timer -= dt
            return False

        self._timer += dt * self.fps
        if self._timer >= 1.0:
            self._timer -= 1.0
            self.current_frame += 1

            if self.current_frame >= self.frame_count:
                self.current_frame = 0
                if self.wait_interval > 0.0:
                    self._wait_timer = self.wait_interval
                return True

        return False

    def reset(self) -> None:
        """Forces the animation back to its first frame and clears timers."""
        self.current_frame = 0
        self._timer = 0.0
        self._wait_timer = 0.0
