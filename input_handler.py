# core/input_handler.py
"""
Handles user input: drawing and voice.
"""

import cv2
import numpy as np
from pathlib import Path
import threading
import time
import logging

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

import config

logger = logging.getLogger(__name__)


class DrawingCapture:
    """Captures drawing input from mouse on a canvas."""
    
    def __init__(self, width=config.CANVAS_WIDTH, height=config.CANVAS_HEIGHT):
        self.width = width
        self.height = height
        self.canvas = np.ones((height, width, 3), dtype=np.uint8) * 255
        self.canvas[:] = config.CANVAS_BACKGROUND
        
        self.drawing = False
        self.last_point = None
        self.points = []
        
        self.window_name = "Draw Your Vision (15 seconds)"
    
    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events on canvas."""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.last_point = (x, y)
        
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing and self.last_point:
                cv2.line(
                    self.canvas,
                    self.last_point,
                    (x, y),
                    config.DRAWING_COLOR,
                    config.BRUSH_SIZE
                )
                self.last_point = (x, y)
                self.points.append((x, y))
        
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            self.last_point = None
    
    def capture(self, duration: int = config.DRAWING_DURATION) -> Path:
        """
        Show interactive drawing canvas.
        
        Args:
            duration: Seconds to allow drawing
        
        Returns:
            Path to saved drawing image
        """
        
        logger.info(f"🎨 Drawing canvas open for {duration} seconds...")
        
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # Display canvas with countdown
            display = self.canvas.copy()
            elapsed = int(time.time() - start_time)
            remaining = duration - elapsed
            
            # Add timer text
            cv2.putText(
                display,
                f"Time remaining: {remaining}s",
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (100, 100, 100),
                2
            )
            cv2.putText(
                display,
                "(Click and drag to draw)",
                (20, 65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (150, 150, 150),
                1
            )
            
            cv2.imshow(self.window_name, display)
            cv2.waitKey(30)
        
        cv2.destroyWindow(self.window_name)
        
        # Save drawing
        output_path = config.GALLERY_PATH / "temp_drawing.png"
        cv2.imwrite(str(output_path), self.canvas)
        
        logger.info(f"✅ Drawing saved to {output_path}")
        
        return output_path
    
    def analyze(self) -> dict:
        """Analyze the drawing for metadata."""
        
        # Convert to grayscale
        gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
        
        # Detect edges
        edges = cv2.Canny(gray, 100, 200)
        
        # Calculate complexity
        edge_pixels = np.sum(edges > 0)
        total_pixels = edges.size
        edge_density = edge_pixels / total_pixels
        
        if edge_density > 0.15:
            complexity = "complex, detailed"
        elif edge_density > 0.05:
            complexity = "moderate"
        else:
            complexity = "simple, minimal"
        
        # Dominant colors (simplified)
        hsv = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2HSV)
        
        return {
            'complexity': complexity,
            'edge_density': edge_density,
            'num_strokes': len(self.points),
        }


class VoiceCapture:
    """Captures and transcribes voice input."""
    
    def __init__(self):
        self.recognizer = sr.Recognizer() if SPEECH_RECOGNITION_AVAILABLE else None
    
    def capture(self, duration: int = config.VOICE_DURATION) -> str:
        """
        Listen for voice input and transcribe.
        
        Args:
            duration: Seconds to listen
        
        Returns:
            Transcribed text
        """
        
        if not config.ENABLE_VOICE:
            logger.info("🔇 Voice capture disabled in config")
            return "[voice disabled]"
        
        if not SPEECH_RECOGNITION_AVAILABLE:
            logger.warning("⚠️  SpeechRecognition not installed. Skipping voice.")
            return "[speech_recognition not installed]"
        
        if not self.recognizer:
            logger.warning("⚠️  Could not initialize speech recognizer.")
            return "[recognizer failed]"
        
        logger.info(f"🎤 Listening for {duration} seconds...")
        
        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # Listen
                audio = self.recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
            
            # Transcribe
            logger.info("🔄 Transcribing...")
            text = self.recognizer.recognize_google(audio)
            
            logger.info(f"✅ Transcribed: '{text}'")
            return text
        
        except sr.UnknownValueError:
            logger.warning("⚠️  Could not understand audio. Returning empty string.")
            return "[unclear]"
        
        except sr.RequestError as e:
            logger.warning(f"⚠️  API error: {e}. Check internet connection.")
            return "[api_error]"
        
        except Exception as e:
            logger.warning(f"⚠️  Voice capture failed: {e}")
            return "[voice_failed]"


class InputManager:
    """Orchestrates drawing and voice input capture."""
    
    def __init__(self):
        self.drawing_capture = DrawingCapture()
        self.voice_capture = VoiceCapture() if config.ENABLE_VOICE else None
    
    def capture_both(self) -> tuple:
        """
        Capture drawing and voice input (sequential for simplicity on Mac).
        
        Returns:
            (drawing_path, voice_text, drawing_analysis)
        """
        
        logger.info("📥 Starting input capture...")
        
        # Drawing first
        drawing_path = self.drawing_capture.capture(duration=config.DRAWING_DURATION)
        drawing_analysis = self.drawing_capture.analyze()
        
        # Then voice
        voice_text = self.voice_capture.capture(duration=config.VOICE_DURATION) if self.voice_capture else ""
        
        return drawing_path, voice_text, drawing_analysis
