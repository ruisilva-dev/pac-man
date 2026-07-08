#!/bin/bash
# package.sh - Standalone packaging script for Pac-Man

echo "Cleaning previous builds..."
rm -rf build/ dist/ PacMan.spec

echo "Building Pac-Man executable with PyInstaller..."
uv run pyinstaller --noconfirm --onedir --windowed \
  --add-data "pacman/assets:pacman/assets" \
  --name "PacMan" \
  pac-man.py

echo "Preparing distribution folder..."

# If config.json exists in the repo, copy it.
# If it was deleted, generate a fresh template directly in the dist folder!
if [ -f "config.json" ]; then
    cp config.json dist/PacMan/
else
    echo "Warning: config.json missing from source. Generating a default template for the package..."
    cat <<EOF > dist/PacMan/config.json
# Pac-Man Configuration File
{
  "highscore_filename": "highscore.json",
  "lives": 3,
  "seed": 42,
  "points_per_pacgum": 10,
  "points_per_super_pacgum": 50,
  "points_per_ghost": 200,
  "theme": "auto",
  "window_width": 960,
  "window_height": 1000
}
EOF
fi

# In-package instructions (controls, options, configuration)
cat << 'EOF' > dist/PacMan/instructions.txt
PAC-MAN - INSTRUCTIONS

CONTROLS:
- Use Arrow Keys to move Pac-Man.
- Press ESC to access the Pause Menu.

OPTIONS & CONFIGURATION:
To change game rules (like lives, points, or the starting seed), edit the "config.json" 
file located in this folder using any text editor before launching the game.

HOW TO PLAY:
Eat all the pacgums to advance to the next level. Avoid the ghosts. 
Eat the large super-pacgums in the corners to make the ghosts edible for extra points.
EOF

echo "Build complete! The packaged game is located in dist/PacMan/"