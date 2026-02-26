# Configuration for Synthetic Relic

import os
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent
GALLERY_PATH = PROJECT_ROOT / "gallery"
GALLERY_PATH.mkdir(exist_ok=True)

# Timings (in seconds)
DRAWING_DURATION = 15        # How long user has to draw
VOICE_DURATION = 10          # How long to listen for voice
GENERATION_TIMEOUT = 120     # Max wait for AI to generate
ANIMATION_DURATION = 8       # How long to show generated image
GALLERY_DISPLAY_DURATION = 5 # Slideshow duration

# Gallery Management
MAX_GALLERY_AGE_HOURS = 48   # Delete entries older than this
MAX_GALLERY_ENTRIES = 100    # Keep at most this many entries

# UI
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600
DRAWING_COLOR = (0, 0, 0)    # Black
CANVAS_BACKGROUND = (255, 255, 255)  # White
BRUSH_SIZE = 5

# API
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")
REPLICATE_MODEL = "stability-ai/stable-diffusion"  # Can swap for ControlNet version later
REPLICATE_TIMEOUT = 120

# Feature Flags
ENABLE_VOICE = True          # Disable to test drawing-only mode
ENABLE_API = True            # Set to False for UI testing without API
MOCK_API_RESPONSE = False    # Use fake generated image for testing
SHOW_CONSOLE_LOGS = True     # Verbose output

# Animation
ENABLE_FADE_IN = True
ENABLE_MORPHING = True
MORPHING_STRENGTH = 0.02     # Subtle movement

# Debug
DEBUG_MODE = True            # Extra logging, keep windows open longer
SAVE_ALL_METADATA = True     # Save prompts, transcriptions, etc.
