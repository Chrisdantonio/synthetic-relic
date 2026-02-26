# SETUP_MAC.md

# Setting Up Synthetic Relic on Mac

## Prerequisites

- Python 3.9 or higher
- Microphone (for voice input)
- Internet connection (for API)

## Step 1: Get Python

If you don't have Python, install via Homebrew:

```bash
brew install python3
```

Verify:
```bash
python3 --version
```

## Step 2: Get a Replicate API Token

1. Go to https://replicate.com
2. Sign up (free tier includes credits)
3. Go to your account settings
4. Copy your API token

## Step 3: Clone/Download This Project

```bash
cd ~/Documents  # or wherever you want
git clone https://github.com/yourusername/synthetic-relic.git
cd synthetic-relic
```

Or download the folder manually and extract it.

## Step 4: Set Up Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

## Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

This may take a minute. You might see warnings—that's normal.

## Step 6: Set Your API Token

```bash
export REPLICATE_API_TOKEN="paste_your_token_here"
```

Replace `paste_your_token_here` with your actual token from step 2.

**To make this persistent** (so you don't have to set it every time):

```bash
# Add to your shell profile
echo 'export REPLICATE_API_TOKEN="your_token_here"' >> ~/.zshrc
source ~/.zshrc
```

(Use `~/.bash_profile` if you use Bash instead of Zsh)

## Step 7: Run It

```bash
python3 main.py
```

You should see a welcome message, then:

1. A drawing canvas window opens (15 seconds to draw)
2. Terminal says "Listening" - speak into your microphone
3. AI generates an image (may take 30-60 seconds)
4. Generated image displays on screen
5. Gallery slideshow plays
6. Back to step 1

## Troubleshooting

### "REPLICATE_API_TOKEN not set"

You forgot to set the environment variable. Run:

```bash
export REPLICATE_API_TOKEN="your_token_here"
```

### "ModuleNotFoundError: No module named 'speech_recognition'"

Dependencies didn't install. Try:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### "No module named 'cv2'" (OpenCV)

Same issue. Make sure your virtual environment is activated (`(venv)` in prompt) and run:

```bash
pip install opencv-python
```

### Microphone not working

- Check System Preferences → Security & Privacy → Microphone → Terminal has access
- Make sure you allow microphone access when prompted
- Try a simple test: `python3 -m speech_recognition`

### Drawing canvas won't open / "AttributeError: window"

This is an OpenCV issue on Mac. Try updating it:

```bash
pip install --upgrade opencv-python
```

If that doesn't work, OpenCV sometimes has issues with Mac's graphics. As a workaround:

```bash
# Uninstall and use headless version
pip uninstall opencv-python
pip install opencv-python-headless
```

Then you'll need to modify the code to use a different display method (this is a known quirk).

### "Connection error" / API calls failing

Check your internet connection and API token. You can test:

```python
python3
>>> import os
>>> print(os.getenv("REPLICATE_API_TOKEN"))
# Should print your token, not "None"
```

### Generation taking forever (>2 minutes)

Normal if using free tier. Replicate may be queuing. Check https://replicate.com/status for service status.

### Want to skip API calls for testing?

Edit `config.py` and set:

```python
ENABLE_API = False
MOCK_API_RESPONSE = True
```

This will use placeholder images instead of real API calls. Good for testing UI without burning API credits.

### Want to test drawing-only?

Edit `config.py`:

```python
ENABLE_VOICE = False
```

## File Structure

```
synthetic-relic/
├── main.py                 # Run this
├── config.py               # Edit for tweaks
├── requirements.txt        # Dependencies
├── core/
│   ├── installation.py     # Main orchestrator
│   ├── input_handler.py    # Drawing + voice
│   ├── api_client.py       # Replicate API
│   └── ui.py               # Display & animations
└── gallery/                # Auto-created, stores results
    └── 2025-02-26_14-30-45/
        ├── drawing.png
        ├── generated.png
        └── metadata.json
```

## Next Steps

### Testing Workflow

1. **Test drawing** → Run, draw something, check `gallery/` for saved drawing
2. **Test voice** → Speak clearly, check console for transcription
3. **Test API** → Check console for Replicate status
4. **Test animation** → Verify smooth playback
5. **Test cleanup** → Leave running for a while, check old files get deleted

### Tweaking Timings

All timings are in `config.py`:

```python
DRAWING_DURATION = 15        # Make shorter for faster testing
VOICE_DURATION = 10
ANIMATION_DURATION = 8
```

### Customizing Prompts

Edit the `create_prompt_from_inputs()` method in `core/api_client.py` to change how voice + drawing becomes an AI prompt.

### Using Different Models

In `core/api_client.py`, change the `version` UUID to use a different model:

```python
"version": "f178fa7a1ae43a9a9af01b833b9d2ecf97b1f047b13f973b0687718bcdb2acd9",
```

Check https://replicate.com for other model versions.

## Questions?

Check console output first—it's verbose and should tell you what's wrong.

If stuck, you can disable features in `config.py` to isolate problems.

Good luck! 🚀
