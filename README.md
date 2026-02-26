# Synthetic Relic: Local Testing (Mac/Linux/Windows)

Interactive AI art installation. Draw + speak, and an AI recreates and animates your vision.

## Quick Start

### Prerequisites
- Python 3.9+
- Mac/Linux/Windows
- Internet connection (for Replicate API)

### Installation

```bash
# Clone/download this project
cd synthetic-relic

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set your Replicate API token
export REPLICATE_API_TOKEN="your_token_here"
```

### Getting a Replicate API Token
1. Go to https://replicate.com
2. Sign up (free tier includes credits)
3. Copy your API token from your account settings
4. Run: `export REPLICATE_API_TOKEN="your_token_here"`

### Run Local Testing

```bash
python3 main.py
```

A window will pop up. Draw on the canvas, allow voice input when prompted, and watch the AI generate your vision.

## Project Structure

```
synthetic-relic/
├── main.py                 # Entry point
├── requirements.txt        # Python dependencies
├── config.py              # Configuration (timings, paths, etc.)
├── core/
│   ├── __init__.py
│   ├── installation.py    # Main installation class
│   ├── ui.py              # UI/display logic
│   ├── input_handler.py   # Drawing & voice input
│   └── api_client.py      # Replicate API calls
├── gallery/               # Local gallery storage
│   └── (auto-created)
└── tests/
    └── (for future unit tests)
```

## Development Workflow

1. **Test drawing input** → Run, draw on canvas, check saved files
2. **Test voice input** → Add voice recording and transcription
3. **Test API calls** → Mock responses first, then real API
4. **Test animation** → Verify smooth playback
5. **Test gallery** → Check file organization and cleanup

## Debugging

- Check `config.py` for timing adjustments
- Gallery files saved to `./gallery/` (check metadata.json for prompts)
- All console output logs to terminal for troubleshooting

## Deploy to Raspberry Pi

Once tested on Mac, deployment guide is in `DEPLOY_TO_PI.md`
