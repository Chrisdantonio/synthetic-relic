# core/api_client.py
"""
Quick Draw sketch renderer.

Matches transcribed voice text to one of Google Quick Draw's ~345 categories,
then renders a random drawing from that category onto a canvas.
No API key required. Data is downloaded on first use and cached locally.
"""

import cv2
import numpy as np
import difflib
import logging
from pathlib import Path

import config

try:
    from quickdraw import QuickDrawData
    QUICKDRAW_AVAILABLE = True
except Exception:
    QUICKDRAW_AVAILABLE = False
    
logger = logging.getLogger(__name__)

# All 345 Quick Draw categories
QUICKDRAW_CATEGORIES = [
    "airplane", "alarm clock", "ambulance", "angel", "animal migration",
    "ant", "anvil", "apple", "arm", "asparagus", "axe", "backpack",
    "banana", "bandage", "barn", "baseball bat", "baseball", "basket",
    "basketball", "bat", "bathtub", "beach", "bear", "beard", "bed",
    "bee", "belt", "bench", "bicycle", "bird", "blackberry", "blueberry",
    "book", "boomerang", "bottlecap", "bowtie", "bracelet", "brain",
    "bread", "bridge", "broccoli", "broom", "bucket", "bulldozer",
    "bus", "bush", "butterfly", "cactus", "cake", "calculator", "calendar",
    "camel", "camera", "candle", "car", "carrot", "castle", "cat",
    "ceiling fan", "cell phone", "chair", "chandelier", "church", "circle",
    "clarinet", "clock", "cloud", "coffee cup", "compass", "computer",
    "cookie", "cooler", "couch", "cow", "crab", "crayon", "crocodile",
    "crown", "cruise ship", "cup", "diamond", "dishwasher", "diving board",
    "dog", "dolphin", "donut", "dragon", "dresser", "drill", "drums",
    "duck", "dumbbell", "ear", "elbow", "elephant", "envelope", "eraser",
    "eye", "eyeglasses", "face", "fan", "feather", "fence", "finger",
    "fire hydrant", "fireplace", "fish", "flamingo", "flashlight",
    "flip flops", "floor lamp", "flower", "flying saucer", "foot",
    "fork", "frog", "frying pan", "garden", "ghost", "giraffe",
    "goatee", "golf club", "grapes", "grass", "guitar", "hamburger",
    "hammer", "hand", "harp", "hat", "headphones", "hedgehog",
    "helicopter", "helmet", "hockey stick", "horse", "hospital", "hot dog",
    "hot tub", "hourglass", "house", "hurricane", "ice cream",
    "jacket", "jail", "kangaroo", "key", "keyboard", "knee", "knife",
    "ladder", "lantern", "laptop", "leaf", "leg", "light bulb", "lighter",
    "lighthouse", "lightning", "line", "lion", "lipstick", "lobster",
    "lollipop", "mailbox", "map", "marker", "matches", "megaphone",
    "mermaid", "microphone", "microwave", "monkey", "moon", "mosquito",
    "motorbike", "mountain", "mouse", "mug", "mushroom", "nail",
    "necklace", "nose", "octopus", "onion", "oven", "owl", "paintbrush",
    "panda", "paper clip", "parachute", "parrot", "passport", "peanut",
    "pear", "peas", "pencil", "penguin", "piano", "pickup truck",
    "picture frame", "pig", "pillow", "pizza", "planet", "pliers",
    "police car", "pool", "popsicle", "postcard", "potato", "power outlet",
    "purse", "rabbit", "rainbow", "rake", "remote control", "rhinoceros",
    "rifle", "river", "roller coaster", "rollerskates", "sailboat",
    "sandwich", "saw", "saxophone", "school bus", "scissors", "scorpion",
    "screwdriver", "sea turtle", "see saw", "shark", "sheep", "shoe",
    "shorts", "shovel", "sink", "skateboard", "skull", "skyscraper",
    "sleeping bag", "smiley face", "snail", "snake", "snowflake",
    "snowman", "soccer ball", "sock", "speedboat", "spider", "spoon",
    "square", "squirrel", "stairs", "star", "steak", "stereo",
    "stethoscope", "stop sign", "stove", "strawberry", "streetlight",
    "submarine", "suitcase", "sun", "swan", "sweater", "swing set",
    "sword", "syringe", "t-shirt", "table", "teapot", "teddy-bear",
    "telephone", "television", "tennis racquet", "tent", "tiger",
    "toaster", "toilet", "tooth", "toothbrush", "toothpaste", "tornado",
    "tractor", "traffic light", "train", "tree", "triangle", "trombone",
    "truck", "trumpet", "umbrella", "underwear", "van", "vase", "violin",
    "washing machine", "watermelon", "whale", "wheel", "windmill",
    "wine bottle", "wine glass", "wristwatch", "zebra", "zigzag",
]

_CATEGORIES_SET = set(QUICKDRAW_CATEGORIES)


class QuickDrawRenderer:
    """
    Matches a voice phrase to a Quick Draw category and renders
    a random authentic sketch from the dataset onto an OpenCV canvas.
    """

    CANVAS_SIZE = 600
    DEFAULT_CATEGORY = "cat"

    def find_category(self, voice_text: str) -> str:
        """
        Find the best-matching Quick Draw category for the given text.
        Strategy: exact word match → multi-word phrase match → fuzzy match → default.
        """
        if not voice_text:
            return self.DEFAULT_CATEGORY

        voice_lower = voice_text.lower().strip()
        words = voice_lower.split()

        # 1. Direct single-word match
        for word in words:
            if word in _CATEGORIES_SET:
                logger.info(f"🎯 Direct match: '{word}'")
                return word

        # 2. Substring / phrase match (handles "a dog" → "dog", "hot dog" → "hot dog")
        for cat in sorted(QUICKDRAW_CATEGORIES, key=len, reverse=True):
            if cat in voice_lower:
                logger.info(f"🎯 Phrase match: '{cat}'")
                return cat

        # 3. Fuzzy match on each word
        for word in words:
            if len(word) < 3:
                continue
            matches = difflib.get_close_matches(word, QUICKDRAW_CATEGORIES, n=1, cutoff=0.75)
            if matches:
                logger.info(f"🎯 Fuzzy word match: '{word}' → '{matches[0]}'")
                return matches[0]

        # 4. Fuzzy match on full phrase
        matches = difflib.get_close_matches(voice_lower, QUICKDRAW_CATEGORIES, n=1, cutoff=0.5)
        if matches:
            logger.info(f"🎯 Fuzzy phrase match: '{voice_lower}' → '{matches[0]}'")
            return matches[0]

        logger.warning(f"⚠️  No category found for '{voice_text}', defaulting to '{self.DEFAULT_CATEGORY}'")
        return self.DEFAULT_CATEGORY

    def generate(self, voice_text: str) -> dict:
        """
        Generate a Quick Draw sketch for the given voice text.

        Returns a dict with:
            - image_path (str): path to saved PNG
            - strokes (list): canvas-scaled stroke data for animation
            - category (str): matched category name
        """
        if not QUICKDRAW_AVAILABLE:
            logger.error("❌ quickdraw unavailable")
            return self._fallback(voice_text)

        category = self.find_category(voice_text)
        logger.info(f"✏️  Loading Quick Draw data for '{category}'...")

        try:
            qd = QuickDrawData()
            drawing = qd.get_drawing(category)
        except Exception as e:
            logger.error(f"❌ Could not load Quick Draw data: {e}")
            return self._fallback(voice_text)

        if not drawing or not drawing.strokes:
            logger.warning(f"⚠️  Empty drawing for '{category}', using fallback")
            return self._fallback(voice_text)

        canvas_size = self.CANVAS_SIZE
        scaled_strokes, canvas = self._render_strokes(drawing.strokes, canvas_size)

        # Label the category in the corner
        cv2.putText(
            canvas, category,
            (12, canvas_size - 14),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (160, 160, 160), 1, cv2.LINE_AA
        )

        output_path = config.GALLERY_PATH / "quickdraw_sketch.png"
        cv2.imwrite(str(output_path), canvas)
        logger.info(f"✅ Sketch saved: {output_path}")

        return {
            "image_path": str(output_path),
            "strokes": scaled_strokes,
            "category": category,
        }

    def _render_strokes(self, raw_strokes: list, canvas_size: int):
        """
        Normalise raw stroke coordinates to fit the canvas.
        Returns (scaled_strokes, filled_canvas).
        """
        all_x = [x for stroke in raw_strokes for x, y in stroke]
        all_y = [y for stroke in raw_strokes for x, y in stroke]

        if not all_x:
            blank = np.ones((canvas_size, canvas_size, 3), dtype=np.uint8) * 255
            return [], blank

        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)

        padding = 70
        draw_area = canvas_size - 2 * padding
        span_x = max(max_x - min_x, 1)
        span_y = max(max_y - min_y, 1)
        scale = min(draw_area / span_x, draw_area / span_y)

        # Centre the drawing
        offset_x = padding + (draw_area - span_x * scale) / 2
        offset_y = padding + (draw_area - span_y * scale) / 2

        def tx(x, y):
            return (
                int((x - min_x) * scale + offset_x),
                int((y - min_y) * scale + offset_y),
            )

        canvas = np.ones((canvas_size, canvas_size, 3), dtype=np.uint8) * 255
        scaled_strokes = []

        for stroke in raw_strokes:
            scaled = [tx(x, y) for x, y in stroke]
            scaled_strokes.append(scaled)
            for i in range(1, len(scaled)):
                cv2.line(canvas, scaled[i - 1], scaled[i], (30, 30, 30), 2, cv2.LINE_AA)

        return scaled_strokes, canvas

    def _fallback(self, voice_text: str) -> dict:
        """Create a simple placeholder sketch when Quick Draw data is unavailable."""
        logger.info("🔄 Using fallback sketch generator")
        canvas_size = self.CANVAS_SIZE
        canvas = np.ones((canvas_size, canvas_size, 3), dtype=np.uint8) * 255

        # Draw a simple placeholder spiral
        cx, cy = canvas_size // 2, canvas_size // 2
        strokes = []
        stroke = []
        for i in range(300):
            angle = i * 0.15
            r = i * 0.7
            x = int(cx + r * np.cos(angle))
            y = int(cy + r * np.sin(angle))
            stroke.append((x, y))
            if i > 0:
                cv2.line(canvas, stroke[-2], stroke[-1], (100, 100, 100), 2, cv2.LINE_AA)
        strokes.append(stroke)

        msg = voice_text[:30] if voice_text else "..."
        cv2.putText(canvas, msg, (20, canvas_size - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

        output_path = config.GALLERY_PATH / "fallback_sketch.png"
        cv2.imwrite(str(output_path), canvas)

        return {
            "image_path": str(output_path),
            "strokes": strokes,
            "category": "unknown",
        }
