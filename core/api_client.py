# core/api_client.py
"""
Handles all API calls to Replicate for image generation.
"""

import requests
import time
import json
from pathlib import Path
import config
import logging
import replicate

logger = logging.getLogger(__name__)


class ReplicateClient:
    """Interface with Replicate API for image generation."""
    
    def __init__(self):
        self.api_token = config.REPLICATE_API_TOKEN
        self.base_url = "https://api.replicate.com/v1"
        self.headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json",
        }
        self.timeout = config.REPLICATE_TIMEOUT
        
        if not self.api_token:
            logger.warning("⚠️  No REPLICATE_API_TOKEN set. Set with: export REPLICATE_API_TOKEN='your_token'")
    
    def generate_image(self, prompt: str) -> str:
        """
        Generate an image using prunaai/flux-fast via replicate.run()
        
        Args:
            prompt: Text description of desired image
        
        Returns:
            URL to generated image
        """
        
        if config.MOCK_API_RESPONSE:
            return self._mock_generation()
        
        if not self.api_token:
            logger.error("❌ No API token. Cannot generate. Using mock image.")
            return self._mock_generation()
        
        try:
            logger.info(f"🎨 Requesting image generation from flux-fast...")
            
            # Use replicate.run() - simple and clean
            output = replicate.run(
                "prunaai/flux-fast",
                input={"prompt": prompt}
            )
            
            # output is a file-like object, get the URL
            image_url = str(output)
            
            logger.info(f"✅ Image generated: {image_url}")
            return image_url
            
        except Exception as e:
            logger.error(f"❌ Generation failed: {e}")
            return self._mock_generation()
    
    def _poll_prediction(self, prediction_id: str, poll_interval: int = 2) -> str:
        """Poll Replicate API until image is generated."""
        
        start_time = time.time()
        attempts = 0
        
        while time.time() - start_time < self.timeout:
            attempts += 1
            
            try:
                response = requests.get(
                    f"{self.base_url}/predictions/{prediction_id}",
                    headers=self.headers,
                    timeout=10
                )
                response.raise_for_status()
                
                result = response.json()
                status = result["status"]
                
                if status == "succeeded":
                    output = result.get("output", [])
                    if output:
                        image_url = output[0]
                        logger.info(f"✅ Generation complete! Image: {image_url}")
                        return image_url
                    else:
                        logger.error("❌ Generation succeeded but no output.")
                        return self._mock_generation()
                
                elif status == "failed":
                    logger.error(f"❌ Generation failed: {result.get('error', 'Unknown error')}")
                    return self._mock_generation()
                
                else:
                    # Still processing
                    logger.info(f"⏳ Status: {status} (attempt {attempts}, {int(time.time() - start_time)}s elapsed)")
                    time.sleep(poll_interval)
            
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Polling error: {e}")
                time.sleep(poll_interval)
        
        logger.error(f"❌ Timeout waiting for generation after {self.timeout}s")
        return self._mock_generation()
    
    def _mock_generation(self) -> str:
        """Create a local placeholder image for testing without API."""
        from PIL import Image, ImageDraw
        import random
        
        # Create a simple mock image locally
        img = Image.new('RGB', (768, 768), color=(240, 240, 240))
        draw = ImageDraw.Draw(img)
        
        # Draw some simple shapes to make it look generated
        random.seed(42)
        for _ in range(20):
            x1 = random.randint(0, 768)
            y1 = random.randint(0, 768)
            x2 = random.randint(0, 768)
            y2 = random.randint(0, 768)
            color = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
            draw.line([(x1, y1), (x2, y2)], fill=color, width=2)
        
        # Save locally
        mock_path = config.GALLERY_PATH / "mock_generated.png"
        img.save(mock_path)
        
        logger.info(f"✅ Mock image created locally at {mock_path}")
        
        # Return file path (display code will handle it)
        return str(mock_path)
    
    def create_prompt_from_inputs(self, drawing_analysis: dict, voice_text: str) -> str:
        """
        Combine drawing analysis + voice into a sketch-focused prompt.
        
        Args:
            drawing_analysis: Dict with keys like 'complexity', 'dominant_colors', 'edges'
            voice_text: Transcribed voice input
        
        Returns:
            Formatted prompt for image generation
        """
        
        logger.info(f"🔨 Building prompt from:")
        logger.info(f"   Voice: '{voice_text}'")
        logger.info(f"   Drawing analysis: {drawing_analysis}")
        
        complexity = drawing_analysis.get('complexity', 'moderate')
        
        # Extract style keywords from voice
        voice_lower = voice_text.lower()
        style_words = []
        
        style_keywords = {
            'organic': ['organic', 'living', 'nature', 'alive', 'breathing'],
            'geometric': ['geometric', 'sharp', 'angular', 'technical', 'precise'],
            'abstract': ['abstract', 'experimental', 'surreal', 'dreamlike'],
            'dark': ['dark', 'moody', 'shadow', 'black', 'night'],
            'bright': ['bright', 'light', 'vibrant', 'colorful', 'glowing'],
            'minimal': ['minimal', 'simple', 'clean', 'sparse'],
        }
        
        for style, keywords in style_keywords.items():
            if any(kw in voice_lower for kw in keywords):
                style_words.append(style)
        
        style_descriptor = ', '.join(style_words) if style_words else 'artistic'
        
        # SKETCH-FOCUSED PROMPT
        prompt = (
            f"A {style_descriptor} line drawing or sketch recreating this composition. "
            f"Style: minimalist sketch, pen and ink drawing, line art. "
            f"User description: '{voice_text}'. "
            f"The original drawing is {complexity}. "
            f"Create clean, simple linework. Black lines on white/light background. "
            f"Sketch style, minimal shading, focus on contours and line quality. "
            f"NOT photorealistic, NOT detailed, NOT rendered. Simple elegant line art."
        )
        
        logger.info(f"📝 Final prompt: {prompt}")
        
        return prompt