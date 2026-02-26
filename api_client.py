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
    
    def generate_image(self, prompt: str, negative_prompt: str = "", num_steps: int = 50) -> str:
        """
        Generate an image from a text prompt.
        
        Args:
            prompt: Text description of desired image
            negative_prompt: What NOT to include
            num_steps: Number of diffusion steps (higher = better quality, slower)
        
        Returns:
            URL to generated image
        """
        
        if config.MOCK_API_RESPONSE:
            return self._mock_generation()
        
        if not self.api_token:
            logger.error("❌ No API token. Cannot generate. Using mock image.")
            return self._mock_generation()
        
        payload = {
            "version": "f178fa7a1ae43a9a9af01b833b9d2ecf97b1f047b13f973b0687718bcdb2acd9",  # Stable Diffusion 2.0
            "input": {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "num_inference_steps": num_steps,
                "guidance_scale": 7.5,
                "width": 768,
                "height": 768,
            }
        }
        
        try:
            logger.info(f"📤 Sending prompt to Replicate...")
            response = requests.post(
                f"{self.base_url}/predictions",
                json=payload,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            prediction = response.json()
            prediction_id = prediction["id"]
            
            logger.info(f"⏳ Generation started (ID: {prediction_id}). Polling for result...")
            
            # Poll until complete
            return self._poll_prediction(prediction_id)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API error: {e}")
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
        """Return a placeholder image URL for testing without API."""
        # In real testing, we'd create a dummy PNG locally
        # For now, return a public placeholder
        return "https://via.placeholder.com/768x768/222/fff?text=Mock+Generation"
    
    def create_prompt_from_inputs(self, drawing_analysis: dict, voice_text: str) -> str:
        """
        Combine drawing analysis + voice into a coherent prompt.
        
        Args:
            drawing_analysis: Dict with keys like 'complexity', 'dominant_colors', 'edges'
            voice_text: Transcribed voice input
        
        Returns:
            Formatted prompt for image generation
        """
        
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
        
        prompt = (
            f"A digital artwork recreating this sketch in a {style_descriptor} style. "
            f"User described it as: '{voice_text}'. "
            f"The original drawing is {complexity}. "
            f"Make it vivid, high quality, animate-ready, slightly ethereal and dreamlike. "
            f"Digital art, concept art."
        )
        
        return prompt
