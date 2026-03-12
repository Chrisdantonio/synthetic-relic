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
    
    def capture(self) -> Path:
        """
        Show interactive drawing canvas with Continue button.
        No time limit - user controls when to proceed.
        
        Returns:
            Path to saved drawing image
        """
        
        logger.info(f"🎨 Drawing canvas open. Click 'Continue' when done...")
        
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        
        button_clicked = False
        
        while not button_clicked:
            # Display canvas with button
            display = self.canvas.copy()
            
            # Draw "Continue" button
            button_x, button_y = 20, self.height - 60
            button_w, button_h = 150, 50
            cv2.rectangle(display, (button_x, button_y), (button_x + button_w, button_y + button_h), (50, 150, 50), -1)
            cv2.putText(
                display,
                "Continue",
                (button_x + 30, button_y + 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (255, 255, 255),
                2
            )
            
            # Add instructions
            cv2.putText(
                display,
                "Click and drag to draw. Click Continue when done.",
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (100, 100, 100),
                1
            )
            
            cv2.imshow(self.window_name, display)
            key = cv2.waitKey(30)
            
            # Check for mouse click on button (through callback)
            if self._button_clicked(button_x, button_y, button_w, button_h):
                button_clicked = True
        
        cv2.destroyWindow(self.window_name)
        
        # Save drawing
        output_path = config.GALLERY_PATH / "temp_drawing.png"
        cv2.imwrite(str(output_path), self.canvas)
        
        logger.info(f"✅ Drawing saved to {output_path}")
        
        return output_path
    
    def _button_clicked(self, x, y, w, h) -> bool:
        """Check if last mouse click was on the button."""
        if not self.points:
            return False
        last_point = self.points[-1]
        return x <= last_point[0] <= x + w and y <= last_point[1] <= y + h
    
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
    
    def capture(self) -> str:
        """
        Listen for voice input with start/stop buttons.
        No time limit - user controls recording duration.
        
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
        
        logger.info(f"🎤 Listening for voice input...")
        logger.info("📢 Speak clearly. Silence ends recording.")
        
        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise once
                logger.info("🔧 Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                
                logger.info("🎤 Listening... speak now (recording until silence)")
                # Listen with generous time - will stop when silence detected
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=20)
            
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
        Capture drawing and voice input (no time limits).
        
        Returns:
            (drawing_path, voice_text, drawing_analysis)
        """
        
        logger.info("📥 Starting input capture...")
        
        # Drawing first (no time limit - button controlled)
        drawing_path = self.drawing_capture.capture()
        drawing_analysis = self.drawing_capture.analyze()
        
        # Then voice (no time limit - speech ends naturally)
        voice_text = self.voice_capture.capture() if self.voice_capture else ""
        
        return drawing_path, voice_text, drawing_analysis