# core/ui.py
"""
UI and display logic: welcome screen, sketch animation, gallery slideshow.
"""

import cv2
import numpy as np
from pathlib import Path
import time
import logging

import config

logger = logging.getLogger(__name__)


class AnimationDisplay:
    """Handles image display and animations."""

    def __init__(self):
        self.window_name = "Synthetic Relic - Generated"

    def display_generated_image(self, image_path: str, duration: int = config.ANIMATION_DURATION, strokes=None) -> Path:
        """
        Display and animate the generated sketch.

        Args:
            image_path: Local file path to the generated sketch image
            duration: How long to display (seconds)
            strokes: Optional list of stroke data for animated drawing effect
        Returns:
            Path to saved image
        """
        try:
            if strokes:
                logger.info("🖊️  Animating sketch stroke by stroke...")
                self._animate_strokes(strokes, duration)
                output_path = config.GALLERY_PATH / "temp_generated.png"
                return output_path
            else:
                frame = cv2.imread(str(image_path))
                if frame is None:
                    logger.error("❌ Failed to decode image")
                    return None
                h, w = frame.shape[:2]
                logger.info(f"✅ Image loaded ({w}x{h})")
                self._animate_frame(frame, duration)
                output_path = config.GALLERY_PATH / "temp_generated.png"
                cv2.imwrite(str(output_path), frame)
                cv2.destroyAllWindows()
                return output_path

        except Exception as e:
            logger.error(f"❌ Error displaying image: {e}")
            return None

    def _animate_strokes(self, strokes: list, duration: int):
        """
        Draw the sketch stroke-by-stroke for a satisfying reveal effect.

        Args:
            strokes: List of strokes, each stroke is list of (x, y) tuples (already canvas-scaled)
            duration: Total animation window duration
        """
        canvas_size = 600
        canvas = np.ones((canvas_size, canvas_size, 3), dtype=np.uint8) * 255

        window_name = "Synthetic Relic - Sketch"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, canvas_size, canvas_size)

        # Count total segments to pace drawing
        all_segments = []
        for stroke in strokes:
            for i in range(1, len(stroke)):
                all_segments.append((stroke[i - 1], stroke[i]))

        draw_duration = max(duration * 0.6, 2.0)  # Spend 60% of time drawing
        hold_duration = duration - draw_duration

        delay_per_segment = draw_duration / max(len(all_segments), 1)
        delay_ms = max(int(delay_per_segment * 1000), 5)

        logger.info(f"✏️  Drawing {len(all_segments)} segments over {draw_duration:.1f}s")

        for p1, p2 in all_segments:
            cv2.line(canvas, p1, p2, (30, 30, 30), 2, cv2.LINE_AA)
            cv2.imshow(window_name, canvas)
            cv2.waitKey(delay_ms)

        # Hold for remaining duration
        start_hold = time.time()
        while time.time() - start_hold < hold_duration:
            cv2.imshow(window_name, canvas)
            cv2.waitKey(100)

        cv2.destroyAllWindows()

    def _animate_frame(self, frame: np.ndarray, duration: int):
        """Animate with fade-in."""
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 800, 800)

        h, w = frame.shape[:2]
        start_time = time.time()
        fps = 30
        frame_delay = int(1000 / fps)

        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            progress = elapsed / duration

            alpha = min(progress * 2, 1.0) if config.ENABLE_FADE_IN else 1.0

            if config.ENABLE_MORPHING:
                scale = 1.0 + config.MORPHING_STRENGTH * np.sin(progress * np.pi * 2)
                M = cv2.getRotationMatrix2D((w / 2, h / 2), 0, scale)
                display_frame = cv2.warpAffine(frame, M, (w, h))
            else:
                display_frame = frame.copy()

            if alpha < 1.0:
                background = np.ones_like(display_frame) * 255
                display_frame = cv2.addWeighted(display_frame, alpha, background, 1 - alpha, 0)

            cv2.imshow(self.window_name, display_frame)
            cv2.waitKey(frame_delay)

        cv2.destroyAllWindows()

    def display_message(self, message: str, duration: int = 3):
        """Display a text message on screen."""
        window_name = "Status"
        cv2.namedWindow(window_name)
        img = np.ones((300, 800, 3), dtype=np.uint8) * 240
        cv2.putText(img, message, (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (50, 50, 50), 2)
        start_time = time.time()
        while time.time() - start_time < duration:
            cv2.imshow(window_name, img)
            cv2.waitKey(100)
        cv2.destroyWindow(window_name)


class GalleryDisplay:
    """Display gallery of recent creations."""

    def __init__(self):
        self.window_name = "Synthetic Relic - Gallery"

    def show_gallery(self, duration: int = config.GALLERY_DISPLAY_DURATION, max_images: int = 20):
        """Show recent creations as a slideshow."""
        generated_images = sorted(
            config.GALLERY_PATH.glob("*.png"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:max_images]

        if not generated_images:
            logger.info("📁 Gallery is empty")
            return

        logger.info(f"📁 Displaying {len(generated_images)} gallery items")
        per_image = duration / len(generated_images)

        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 600, 600)

        for img_path in generated_images:
            frame = cv2.imread(str(img_path))
            if frame is None:
                continue
            start_time = time.time()
            while time.time() - start_time < per_image:
                cv2.imshow(self.window_name, frame)
                cv2.waitKey(100)

        cv2.destroyWindow(self.window_name)
        logger.info("✅ Gallery slideshow complete")

    def show_welcome_screen(self):
        """
        Display voice-only welcome screen with properly padded button.
        Waits for 'Click to Start' before proceeding.
        """
        logger.info("📺 Showing welcome screen...")

        W, H = 900, 480
        img = np.ones((H, W, 3), dtype=np.uint8) * 238  # light grey background

        # Title
        title = "Synthetic Relic"
        (tw, th), _ = cv2.getTextSize(title, cv2.FONT_HERSHEY_SIMPLEX, 2.2, 3)
        cv2.putText(img, title, ((W - tw) // 2, 130), cv2.FONT_HERSHEY_SIMPLEX, 2.2, (45, 45, 45), 3)

        # Subtitle — voice-only
        sub = "Speak your vision"
        (sw, _), _ = cv2.getTextSize(sub, cv2.FONT_HERSHEY_SIMPLEX, 1.1, 2)
        cv2.putText(img, sub, ((W - sw) // 2, 205), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (100, 100, 100), 2)

        # Steps — voice-only flow
        steps = "1. Describe something   2. Watch AI sketch it"
        (stw, _), _ = cv2.getTextSize(steps, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 1)
        cv2.putText(img, steps, ((W - stw) // 2, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (150, 150, 150), 1)

        # Button — centred with generous padding
        btn_label = "Click to Start"
        font_scale = 1.0
        thickness = 2
        (lw, lh), baseline = cv2.getTextSize(btn_label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        pad_x, pad_y = 32, 18
        btn_w = lw + pad_x * 2
        btn_h = lh + pad_y * 2
        btn_x = (W - btn_w) // 2
        btn_y = 340

        cv2.rectangle(img, (btn_x, btn_y), (btn_x + btn_w, btn_y + btn_h), (50, 150, 50), -1)
        text_x = btn_x + pad_x
        text_y = btn_y + pad_y + lh - 2
        cv2.putText(img, btn_label, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness)

        window_name = "Welcome"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, W, H)

        button_clicked = [False]

        def click_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                if btn_x <= x <= btn_x + btn_w and btn_y <= y <= btn_y + btn_h:
                    logger.info("✅ Start button clicked!")
                    button_clicked[0] = True

        cv2.setMouseCallback(window_name, click_callback)

        while not button_clicked[0]:
            cv2.imshow(window_name, img)
            cv2.waitKey(50)

        cv2.destroyWindow(window_name)
        logger.info("📺 Welcome screen closed, starting...")
