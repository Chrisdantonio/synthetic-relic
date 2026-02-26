#!/usr/bin/env python3
"""
main.py - Entry point for Synthetic Relic local testing

Run this to start the installation on your Mac/Linux/Windows:
    python3 main.py

Make sure to set your API token first:
    export REPLICATE_API_TOKEN="your_token_here"
"""

import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)

# Import installation
from core.installation import SyntheticRelicInstallation
import config


def main():
    """Main entry point."""
    
    # Check API token
    if config.ENABLE_API and not config.REPLICATE_API_TOKEN:
        logger.error("\n❌ REPLICATE_API_TOKEN not set!")
        logger.error("\nTo get started:")
        logger.error("1. Sign up at https://replicate.com")
        logger.error("2. Copy your API token from account settings")
        logger.error("3. Run: export REPLICATE_API_TOKEN='your_token_here'")
        logger.error("4. Then run this script again\n")
        sys.exit(1)
    
    logger.info("✅ Configuration valid")
    
    # Create and run installation
    installation = SyntheticRelicInstallation()
    installation.run()


if __name__ == "__main__":
    main()
