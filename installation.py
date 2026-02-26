# core/installation.py
"""
Main installation orchestrator: coordinates all components.
"""

import json
import shutil
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

import config
from core.input_handler import InputManager
from core.api_client import ReplicateClient
from core.ui import AnimationDisplay, GalleryDisplay

logger = logging.getLogger(__name__)


class SyntheticRelicInstallation:
    """Main orchestrator for the installation."""
    
    def __init__(self):
        self.gallery_path = config.GALLERY_PATH
        self.input_manager = InputManager()
        self.api_client = ReplicateClient()
        self.display = AnimationDisplay()
        self.gallery_display = GalleryDisplay()
        
        self.current_session = None
        
        logger.info("🚀 Synthetic Relic initialized")
    
    def create_session(self) -> Path:
        """Create a timestamped folder for this interaction."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_path = self.gallery_path / timestamp
        session_path.mkdir(parents=True, exist_ok=True)
        self.current_session = session_path
        logger.info(f"📂 Session created: {timestamp}")
        return session_path
    
    def save_metadata(self, voice_text: str, prompt: str, generated_image_url: str = None):
        """Save interaction metadata."""
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "voice_transcription": voice_text,
            "ai_prompt": prompt,
            "image_url": generated_image_url or "local",
        }
        
        metadata_path = self.current_session / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"💾 Metadata saved")
    
    def cleanup_old_entries(self):
        """Delete old gallery entries based on config."""
        
        if not self.gallery_path.exists():
            return
        
        entries = list(self.gallery_path.iterdir())
        
        # Delete by age
        cutoff_time = datetime.now() - timedelta(hours=config.MAX_GALLERY_AGE_HOURS)
        for entry in entries:
            try:
                # Parse timestamp from folder name
                timestamp = datetime.strptime(entry.name, "%Y-%m-%d_%H-%M-%S")
                if timestamp < cutoff_time:
                    shutil.rmtree(entry)
                    logger.info(f"🗑️  Deleted old entry: {entry.name}")
            except ValueError:
                # Skip folders that don't match timestamp format
                pass
        
        # Keep only most recent N entries
        entries = sorted(self.gallery_path.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        if len(entries) > config.MAX_GALLERY_ENTRIES:
            for old_entry in entries[config.MAX_GALLERY_ENTRIES:]:
                shutil.rmtree(old_entry)
                logger.info(f"🗑️  Deleted (limit exceeded): {old_entry.name}")
    
    def run_single_interaction(self) -> bool:
        """
        Run one complete interaction cycle.
        
        Returns:
            True if successful, False if error
        """
        
        try:
            # Create session
            self.create_session()
            
            # Show welcome
            self.gallery_display.show_welcome_screen(duration=2)
            
            # Capture input
            logger.info("📥 Capturing drawing and voice...")
            drawing_path, voice_text, drawing_analysis = self.input_manager.capture_both()
            
            if not drawing_path or not voice_text:
                logger.warning("⚠️  Input capture incomplete")
                return False
            
            # Copy drawing to session
            shutil.copy(drawing_path, self.current_session / "drawing.png")
            logger.info(f"📸 Drawing: {voice_text}")
            
            # Generate AI prompt
            logger.info("🤖 Generating prompt...")
            prompt = self.api_client.create_prompt_from_inputs(drawing_analysis, voice_text)
            logger.info(f"📝 Prompt: {prompt[:100]}...")
            
            # Generate image via API
            logger.info("🎨 Requesting image generation...")
            generated_image_url = self.api_client.generate_image(prompt)
            
            if not generated_image_url:
                logger.error("❌ Image generation failed")
                return False
            
            # Display generated image
            logger.info("🎬 Animating result...")
            generated_path = self.display.display_generated_image(
                generated_image_url,
                duration=config.ANIMATION_DURATION
            )
            
            # Save metadata
            self.save_metadata(voice_text, prompt, generated_image_url)
            
            logger.info("✅ Interaction complete!")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error during interaction: {e}", exc_info=True)
            return False
    
    def run(self):
        """Main loop."""
        
        logger.info("=" * 60)
        logger.info("SYNTHETIC RELIC - LOCAL TEST MODE")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Instructions:")
        logger.info("1. A drawing canvas will appear - draw for 15 seconds")
        logger.info("2. Allow microphone access for voice input (10 seconds)")
        logger.info("3. AI will generate an image from your drawing + description")
        logger.info("4. Generated image will animate on screen")
        logger.info("5. Gallery slideshow of recent creations")
        logger.info("")
        logger.info("Press Ctrl+C to exit")
        logger.info("=" * 60)
        logger.info("")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                logger.info(f"\n🔄 Cycle {cycle_count} starting...")
                
                # Run interaction
                success = self.run_single_interaction()
                
                if success:
                    # Show gallery
                    logger.info("📺 Showing gallery...")
                    self.gallery_display.show_gallery(duration=config.GALLERY_DISPLAY_DURATION)
                
                # Cleanup periodically
                if cycle_count % 5 == 0:
                    logger.info("🧹 Cleaning up old entries...")
                    self.cleanup_old_entries()
                
                # Brief pause before next cycle
                logger.info("⏳ Ready for next interaction in 2 seconds...\n")
                time.sleep(2)
        
        except KeyboardInterrupt:
            logger.info("\n\n👋 Shutting down...")
            logger.info(f"Gallery saved to: {self.gallery_path}")
            logger.info("Goodbye!")
