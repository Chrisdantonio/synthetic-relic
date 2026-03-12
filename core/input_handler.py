# core/input_handler.py
"""
Handles user input: voice capture with animated listening indicator.
"""

import cv2
import numpy as np
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


class VoiceCapture:
    """
    Captures and transcribes voice input.
    Shows an animated OpenCV listening indicator on the main thread
    while voice recording runs in a background thread.
    """

    def __init__(self):
        self.recognizer = sr.Recognizer() if SPEECH_RECOGNITION_AVAILABLE else None

    def capture(self) -> str:
        """
        Listen for voice input and show a live listening indicator.
        Returns transcribed text.
        """

        if not config.ENABLE_VOICE:
            logger.info("🔇 Voice capture disabled in config")
            return "[voice disabled]"

        if not SPEECH_RECOGNITION_AVAILABLE:
            logger.warning("⚠️  SpeechRecognition not installed.")
            return "[speech_recognition not installed]"

        if not self.recognizer:
            logger.warning("⚠️  Could not initialize speech recognizer.")
            return "[recognizer failed]"

        # Shared state between threads
        result = [None]
        state = ["starting"]   # starting → adjusting → listening → transcribing → done
        error = [None]

        def voice_thread():
            try:
                with sr.Microphone() as source:
                    state[0] = "adjusting"
                    logger.info("🔧 Adjusting for ambient noise...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=2)

                    state[0] = "listening"
                    logger.info("🎤 Listening... speak now")
                    audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=20)

                state[0] = "transcribing"
                logger.info("🔄 Transcribing...")
                result[0] = self.recognizer.recognize_google(audio)
                logger.info(f"✅ Transcribed: '{result[0]}'")

            except sr.UnknownValueError:
                logger.warning("⚠️  Could not understand audio.")
                result[0] = "[unclear]"
            except sr.RequestError as e:
                logger.warning(f"⚠️  API error: {e}")
                result[0] = "[api_error]"
            except Exception as e:
                logger.warning(f"⚠️  Voice capture failed: {e}")
                result[0] = "[voice_failed]"
            finally:
                state[0] = "done"

        # Start voice recording in background
        t = threading.Thread(target=voice_thread, daemon=True)
        t.start()

        # Animate on main thread while recording
        self._show_listening_animation(state)

        t.join(timeout=35)
        return result[0] or "[voice_failed]"

    def _show_listening_animation(self, state: list):
        """
        Show an animated OpenCV window reflecting microphone state.
        Runs on the main thread (required for OpenCV GUI on macOS).
        """

        W, H = 600, 280
        window_name = "Synthetic Relic - Listening"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, W, H)

        start_time = time.time()

        while state[0] != "done":
            elapsed = time.time() - start_time
            img = np.ones((H, W, 3), dtype=np.uint8) * 238

            cur = state[0]

            if cur == "starting":
                label = "Initializing microphone..."
                color = (160, 160, 160)
                pulse_speed = 1.5

            elif cur == "adjusting":
                label = "Calibrating for room noise..."
                color = (50, 180, 220)   # amber-ish blue
                pulse_speed = 2.0

            elif cur == "listening":
                label = "Listening  -  speak now"
                color = (50, 190, 80)    # green
                pulse_speed = 2.5

            else:  # transcribing
                label = "Processing..."
                color = (80, 130, 220)   # blue
                pulse_speed = 3.0

            # Pulsing outer ring
            pulse = 0.5 + 0.5 * np.sin(elapsed * pulse_speed * np.pi)
            outer_r = int(52 + 12 * pulse)
            inner_r = 38
            cx, cy = W // 2, H // 2 - 20

            cv2.circle(img, (cx, cy), outer_r, tuple(int(c * 0.5) for c in color), 2, cv2.LINE_AA)
            cv2.circle(img, (cx, cy), inner_r, color, -1, cv2.LINE_AA)

            # Mic symbol (simple rectangle + stand)
            mic_w, mic_h = 12, 18
            cv2.rectangle(img,
                          (cx - mic_w // 2, cy - mic_h // 2),
                          (cx + mic_w // 2, cy + mic_h // 2),
                          (255, 255, 255), -1)
            cv2.rectangle(img,
                          (cx - mic_w // 2, cy - mic_h // 2),
                          (cx + mic_w // 2, cy + mic_h // 2),
                          (200, 200, 200), 1)
            # Stand
            cv2.line(img, (cx, cy + mic_h // 2), (cx, cy + mic_h // 2 + 8), (255, 255, 255), 2)
            cv2.line(img, (cx - 8, cy + mic_h // 2 + 8), (cx + 8, cy + mic_h // 2 + 8), (255, 255, 255), 2)

            # Label
            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)
            cv2.putText(img, label, ((W - lw) // 2, cy + 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (60, 60, 60), 2)

            # Animated dots when listening
            if cur == "listening":
                dot_count = int(elapsed * 1.5) % 4
                dots = "." * dot_count
                (dw, _), _ = cv2.getTextSize(dots, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)
                cv2.putText(img, dots, ((W + lw) // 2 + 8, cy + 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (50, 190, 80), 2)

            cv2.imshow(window_name, img)
            cv2.waitKey(33)   # ~30 fps

        cv2.destroyWindow(window_name)


class InputManager:
    """Orchestrates voice input capture."""

    def __init__(self):
        self.voice_capture = VoiceCapture() if config.ENABLE_VOICE else None
