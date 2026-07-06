import os
import pygame


class AudioManager:
    """Manages audio streaming, global effects, and thematic soundscapes.

    Coordinates the streaming initialization of background audio elements,
    implements a centralized shared assets lookup routing pipeline, and
    caches transient sound effect buffers across variable configurations.

    Attributes:
        audio_root: Base file path containing all audio assets.
        current_theme: Currently active theme directory name identifier.
        current_music: Tracks the file system path of the active stream.
        sfx_cache: Storage tracking preloaded dynamic sound effect buffers.
    """

    def __init__(self, base_path: str) -> None:
        """Initializes the mixer subsystem and prepares tracking markers.

        Args:
            audio_root: File system parent pathway mapping audio files.
        """
        self.audio_root: str = os.path.join(
            base_path, "pacman", "assets", "audio"
        )
        self.current_theme: str = "classic"
        self.current_music: str | None = None
        self.sfx_cache: dict[str, pygame.mixer.Sound] = {}
        self.frightened_channel: pygame.mixer.Channel | None = None

        self.music_volume: float = 0.3
        self.sfx_volume: float = 0.8

        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except pygame.error as e:
                print(
                    f"Warning: Audio device initialization failed ({e}). "
                    f"Running in silent mode."
                )

    def set_theme(self, theme: str) -> None:
        """Updates the internal operational directory path context tracking.

        Args:
            theme: Theme name string matching asset mapping indices.
        """
        self.current_theme = theme
        self.sfx_cache.clear()

    def play_music(self, filename: str, loops: int = -1,
                   fallback: str | None = None,
                   is_global: bool = False) -> None:
        """Streams looping background music, with an optional fallback.

        Args:
            filename: Music file name.
            loops: Loop count (-1 loops forever).
            fallback: Global music file to use if the primary is missing.
            is_global: If True, looks for filename in the global folder
                instead of the current theme's folder.
        """
        if is_global:
            path = os.path.join(self.audio_root, "global", filename)
        else:
            path = os.path.join(
                self.audio_root, "themes", self.current_theme, filename
            )

        # Fall back to a global track if the primary is missing.
        if not os.path.exists(path) and fallback is not None:
            path = os.path.join(self.audio_root, "global", fallback)

        if self.current_music == path:
            return

        try:
            pygame.mixer.music.stop()
            if os.path.exists(path):
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(loops)
                self.current_music = path
        except pygame.error as e:
            print(f"Warning: Failed to load music {filename}: {e}")

    def stop_music(self) -> None:
        """Completely terminates active audio background track streams."""
        pygame.mixer.music.stop()
        self.current_music = None

    def play_sfx(self, filename: str, is_global: bool = False) -> None:
        """Fires a short sound effect instantly from memory cache.

        Args:
            filename: File location index inside the asset folder.
            is_global: If True, pulls from centralized shared folder paths.
        """
        if filename in self.sfx_cache:
            sound = self.sfx_cache[filename]
            sound.set_volume(self.sfx_volume)
            sound.play()
            return

        if is_global:
            path = os.path.join(self.audio_root, "global", filename)
        else:
            path = os.path.join(
                self.audio_root, "themes", self.current_theme, filename
            )

        try:
            if os.path.exists(path):
                sound = pygame.mixer.Sound(path)
                sound.set_volume(self.sfx_volume)
                self.sfx_cache[filename] = sound
                sound.play()
        except pygame.error as e:
            print(f"Warning: Failed to load dynamic asset {filename}: {e}")

    def play_sfx_loop(self, filename: str, is_global: bool = False) -> None:
        """Plays a looping sound effect on a dedicated channel."""
        if filename in self.sfx_cache:
            sound = self.sfx_cache[filename]
        else:
            if is_global:
                path = os.path.join(self.audio_root, "global", filename)
            else:
                path = os.path.join(
                    self.audio_root, "themes", self.current_theme, filename
                )
            if not os.path.exists(path):
                return
            try:
                sound = pygame.mixer.Sound(path)
                self.sfx_cache[filename] = sound
            except pygame.error as e:
                print(f"Warning: Failed to load loop {filename}: {e}")
                return

        sound.set_volume(self.sfx_volume)
        sound.play(loops=-1)

    def start_frightened_sound(self, filename: str = "chase.wav") -> None:
        """Starts the looping frightened sound if not already playing."""
        if (self.frightened_channel is not None
                and self.frightened_channel.get_busy()):
            return  # já está a tocar

        if filename in self.sfx_cache:
            sound = self.sfx_cache[filename]
        else:
            path = os.path.join(self.audio_root, "global", filename)
            if not os.path.exists(path):
                return
            try:
                sound = pygame.mixer.Sound(path)
                self.sfx_cache[filename] = sound
            except pygame.error as e:
                print(f"Warning: Failed to load {filename}: {e}")
                return

        sound.set_volume(self.sfx_volume)
        self.frightened_channel = sound.play(loops=-1)

    def stop_frightened_sound(self) -> None:
        """Stops the looping frightened sound."""
        if self.frightened_channel is not None:
            self.frightened_channel.stop()
            self.frightened_channel = None

    def stop_all_sfx(self) -> None:
        """Stops all currently playing sound effects across all channels."""
        if pygame.mixer.get_init():
            pygame.mixer.stop()
        # Reset the specific frightened channel reference since it was stopped
        self.frightened_channel = None

    def pause_music(self) -> None:
        """Pauses the current music, keeping its position."""
        pygame.mixer.music.pause()

    def unpause_music(self) -> None:
        """Resumes music from where it was paused."""
        pygame.mixer.music.unpause()
