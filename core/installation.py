# core/installation.py
"""
Main orchestrator: voice → Quick Draw sketch → animated reveal.
"""

import json
import shutil
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

import config
from core.input_handler import InputManager
from core.api_client import QuickDrawRenderer
from core.ui import AnimationDisplay, GalleryDisplay

logger = logging.getLogger(__name__)


class SyntheticRelicInstallation:
    """Main orchestrator for the installation."""

    def __init__(self):
        self.gallery_path = config.GALLERY_PATH
        self.input_manager = InputManager()
        self.renderer = QuickDrawRenderer()
        self.display = AnimationDisplay()
        self.gallery_display = GalleryDisplay()
        self.current_session = None
        logger.info("🚀 Synthetic Relic initialized")

    def create_session(self) -> Path:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_path = self.gallery_path / timestamp
        session_path.mkdir(parents=True, exist_ok=True)
        self.current_session = session_path
        logger.info(f"📂 Session: {timestamp}")
        return session_path

    def save_metadata(self, voice_text: str, category: str, sketch_path: str):
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "voice_transcription": voice_text,
            "quickdraw_category": category,
            "sketch_path": sketch_path,
        }
        metadata_path = self.current_session / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        logger.info("💾 Metadata saved")

    def cleanup_old_entries(self):
        if not self.gallery_path.exists():
            return
        cutoff_time = datetime.now() - timedelta(hours=config.MAX_GALLERY_AGE_HOURS)
        entries = list(self.gallery_path.iterdir())
        for entry in entries:
            if not entry.is_dir():
                continue
            try:
                timestamp = datetime.strptime(entry.name, "%Y-%m-%d_%H-%M-%S")
                if timestamp < cutoff_time:
                    shutil.rmtree(entry)
                    logger.info(f"🗑️  Deleted old entry: {entry.name}")
            except ValueError:
                pass
        entries = sorted(
            [e for e in self.gallery_path.iterdir() if e.is_dir()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if len(entries) > config.MAX_GALLERY_ENTRIES:
            for old_entry in entries[config.MAX_GALLERY_ENTRIES:]:
                shutil.rmtree(old_entry)
                logger.info(f"🗑️  Deleted (limit exceeded): {old_entry.name}")

    def run_single_interaction(self) -> bool:
        try:
            self.create_session()

            # Welcome screen
            self.gallery_display.show_welcome_screen()

            # Voice capture (with animated listening indicator)
            logger.info("📥 Capturing voice input...")
            voice_text = self.input_manager.voice_capture.capture()

            if not voice_text or voice_text.startswith("["):
                logger.warning(f"⚠️  Voice input failed: {voice_text}")
                return False

            logger.info(f"✅ Voice captured: '{voice_text}'")

            # Generate Quick Draw sketch
            logger.info("✏️  Generating Quick Draw sketch...")
            result = self.renderer.generate(voice_text)

            if not result:
                logger.error("❌ Sketch generation failed")
                return False

            logger.info(f"🎨 Category matched: '{result['category']}'")

            # Animate stroke-by-stroke reveal
            logger.info("🎬 Animating sketch...")
            self.display.display_generated_image(
                image_path=result["image_path"],
                duration=config.ANIMATION_DURATION,
                strokes=result["strokes"],
            )

            # Copy sketch to session folder
            sketch_dest = self.current_session / "generated.png"
            import shutil as _sh
            _sh.copy(result["image_path"], sketch_dest)

            self.save_metadata(voice_text, result["category"], str(sketch_dest))
            logger.info("✅ Interaction complete!")
            return True

        except Exception as e:
            logger.error(f"❌ Error during interaction: {e}", exc_info=True)
            return False

    def run(self):
        logger.info("=" * 60)
        logger.info("SYNTHETIC RELIC")
        logger.info("=" * 60)
        logger.info("Instructions:")
        logger.info("1. Click 'Click to Start' on the welcome screen")
        logger.info("2. Speak a word or phrase describing something")
        logger.info("3. Watch a Quick Draw sketch appear stroke by stroke")
        logger.info("")
        logger.info("Press Ctrl+C to exit")
        logger.info("=" * 60)

        cycle_count = 0

        try:
            while True:
                cycle_count += 1
                logger.info(f"\n🔄 Cycle {cycle_count}...")

                success = self.run_single_interaction()

                if success:
                    logger.info("📺 Showing gallery...")
                    self.gallery_display.show_gallery(duration=config.GALLERY_DISPLAY_DURATION)

                if cycle_count % 5 == 0:
                    self.cleanup_old_entries()

                logger.info("⏳ Ready for next interaction in 2 seconds...\n")
                time.sleep(2)

        except KeyboardInterrupt:
            logger.info("\n👋 Shutting down.")
            logger.info(f"Gallery saved to: {self.gallery_path}")
