# core/ui.py
"""
UI and display logic: animations, gallery slideshow, etc.
"""

import cv2
import numpy as np
from pathlib import Path
import time
import requests
import io
import logging

import config

logger = logging.getLogger(__name__)


class AnimationDisplay:
    """Handles image display and animations."""
    
    def __init__(self):
        self.window_name = "Synthetic Relic - Generated"
    
    def display_generated_image(self, image_url: str, duration: int = config.ANIMATION_DURATION) -> Path:
        """
        Display and animate the generated image (from URL or local file).
        
        Args:
            image_url: URL to generated image or local file path
            duration: How long to display (seconds)
        
        Returns:
            Path to saved image
        """
        
        try:
            # Check if it's a local file path
            from pathlib import Path
            if Path(image_url).exists():
                logger.info(f"📂 Loading local image...")
                frame = cv2.imread(str(image_url))
            else:
                # It's a URL, download it
                logger.info(f"📥 Downloading generated image...")
                response = requests.get(image_url, timeout=10)
                response.raise_for_status()
                
                # Load as numpy array
                img_array = np.frombuffer(response.content, np.uint8)
                frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if frame is None:
                logger.error("❌ Failed to decode image")
                return None
            
            h, w = frame.shape[:2]
            
            logger.info(f"✅ Image loaded ({w}x{h})")
            
            # Display with animation
            self._animate_frame(frame, duration)
            
            # Save to gallery
            output_path = config.GALLERY_PATH / "temp_generated.png"
            cv2.imwrite(str(output_path), frame)
            
            cv2.destroyAllWindows()
            return output_path
        
        except Exception as e:
            logger.error(f"❌ Error displaying image: {e}")
            return None
    
    def _animate_frame(self, frame: np.ndarray, duration: int):
        """
        Animate the frame with fade-in and subtle morphing.
        
        Args:
            frame: Image to display
            duration: Animation duration in seconds
        """
        
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 800, 800)
        
        h, w = frame.shape[:2]
        start_time = time.time()
        fps = 30
        frame_delay = int(1000 / fps)
        
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            progress = elapsed / duration
            
            # Fade in effect
            if config.ENABLE_FADE_IN:
                alpha = min(progress * 2, 1.0)
            else:
                alpha = 1.0
            
            # Subtle morphing/zoom effect
            if config.ENABLE_MORPHING:
                scale = 1.0 + config.MORPHING_STRENGTH * np.sin(progress * np.pi * 2)
                M = cv2.getRotationMatrix2D((w / 2, h / 2), 0, scale)
                display_frame = cv2.warpAffine(frame, M, (w, h))
            else:
                display_frame = frame.copy()
            
            # Blend with background for fade effect
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
        
        # Create blank image
        img = np.ones((300, 800, 3), dtype=np.uint8) * 240
        
        # Add text
        cv2.putText(
            img,
            message,
            (50, 150),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (50, 50, 50),
            2
        )
        
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
        """
        Show recent creations as a slideshow.
        
        Args:
            duration: Total slideshow duration
            max_images: Max number of images to show
        """
        
        # Get recent generated images
        generated_images = sorted(
            config.GALLERY_PATH.glob("*/generated.png"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:max_images]
        
        if not generated_images:
            logger.info("📁 Gallery is empty")
            return
        
        logger.info(f"📁 Displaying {len(generated_images)} gallery items")
        
        per_image = duration / len(generated_images) if generated_images else duration
        
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
        """Display welcome/instruction screen with Continue button."""
        
        logger.info("📺 Showing welcome screen. Click 'Click to Start' button to begin.")
        
        img = np.ones((500, 1000, 3), dtype=np.uint8) * 240
        
        cv2.putText(
            img,
            "Synthetic Relic",
            (250, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            2.0,
            (50, 50, 50),
            3
        )
        
        cv2.putText(
            img,
            "Draw or speak your vision",
            (200, 200),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (100, 100, 100),
            2
        )
        
        cv2.putText(
            img,
            "1. Draw something  2. Describe it  3. Watch AI recreate it",
            (80, 280),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (150, 150, 150),
            2
        )
        
        # Draw Continue button
        button_x, button_y = 400, 380
        button_w, button_h = 200, 60
        cv2.rectangle(img, (button_x, button_y), (button_x + button_w, button_y + button_h), (50, 150, 50), -1)
        cv2.putText(
            img,
            "Click to Start",
            (button_x + 30, button_y + 42),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.1,
            (255, 255, 255),
            2
        )
        
        window_name = "Welcome"
        cv2.namedWindow(window_name)
        
        button_clicked = [False]  # Use list for mutable closure variable
        button_region = (button_x, button_y, button_w, button_h)
        
        def click_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                logger.info(f"🖱️  Click detected at ({x}, {y})")
                if button_x <= x <= button_x + button_w and button_y <= y <= button_y + button_h:
                    logger.info("✅ Start button clicked!")
                    button_clicked[0] = True
        
        cv2.setMouseCallback(window_name, click_callback)
        
        while not button_clicked[0]:
            cv2.imshow(window_name, img)
            cv2.waitKey(100)
        
        cv2.destroyWindow(window_name)
        logger.info("📺 Welcome screen closed, starting interaction...")