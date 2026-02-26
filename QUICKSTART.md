# QUICKSTART.md

# Quick Start - 5 Minutes to Running

## TL;DR

```bash
# 1. Get your API token from https://replicate.com

# 2. Clone the project (or download it)
cd synthetic-relic

# 3. Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Set token
export REPLICATE_API_TOKEN="your_token_here"

# 5. Run
python3 main.py
```

## What Happens When You Run It

1. **Welcome screen** (2 sec)
2. **Drawing canvas opens** - Draw something for 15 seconds
3. **Listening prompt** - Speak a description for 10 seconds
4. **"Dreaming..."** - AI generates image (30-60 seconds, check console)
5. **Generated image animates** - Fades in, subtle morphing (8 seconds)
6. **Gallery slideshow** - Recent creations play (5 seconds)
7. **Repeat** - Back to step 1

All results saved to `gallery/` folder.

## Test Modes (Useful for Debugging)

Edit `config.py`:

### Skip API calls (test UI without internet)
```python
ENABLE_API = False
MOCK_API_RESPONSE = True
```

### Drawing only (skip voice)
```python
ENABLE_VOICE = False
```

### Faster timings (for quick testing)
```python
DRAWING_DURATION = 5
VOICE_DURATION = 3
ANIMATION_DURATION = 3
GALLERY_DISPLAY_DURATION = 2
```

### Verbose debugging
```python
DEBUG_MODE = True
SHOW_CONSOLE_LOGS = True
```

## File Guide

- **main.py** - Run this
- **config.py** - Edit settings here
- **core/installation.py** - Main logic
- **core/input_handler.py** - Drawing & voice capture
- **core/api_client.py** - Replicate API calls
- **core/ui.py** - Display & animations
- **gallery/** - Your creations saved here

## Troubleshooting

**"API token not set"**
```bash
export REPLICATE_API_TOKEN="paste_your_token_here"
```

**"No module named X"**
```bash
pip install -r requirements.txt
```

**Drawing canvas won't appear**
```bash
pip install --upgrade opencv-python
```

**Microphone not working**
- Check System Preferences → Security & Privacy → Microphone → Terminal
- Run: `python3 -m speech_recognition`

**Want to test without voice?**
Edit `config.py`: `ENABLE_VOICE = False`

## Next Steps

- Tweak timings in `config.py` for your setup
- Play with prompts in `core/api_client.py`
- Read **SETUP_MAC.md** for detailed setup
- Read **DEPLOY_TO_PI.md** when ready for Pi deployment

## Files in This Project

```
synthetic-relic/
├── main.py                    ← RUN THIS
├── config.py                  ← EDIT SETTINGS HERE
├── requirements.txt           
├── QUICKSTART.md              ← YOU ARE HERE
├── SETUP_MAC.md               ← Detailed setup
├── DEPLOY_TO_PI.md            ← When ready for Pi
├── README.md                  
├── core/
│   ├── __init__.py
│   ├── installation.py        
│   ├── input_handler.py       
│   ├── api_client.py          
│   └── ui.py                  
└── gallery/                   ← Auto-created, stores results
```

## Common Issues

| Issue | Fix |
|-------|-----|
| "REPLICATE_API_TOKEN not set" | `export REPLICATE_API_TOKEN="token_here"` |
| Drawing canvas won't open | `pip install --upgrade opencv-python` |
| Microphone not working | Check System Prefs → Security & Privacy → Microphone |
| API timeout | Check internet, check Replicate status, increase timeout in config |
| Generation taking forever | Free tier may be slower, or API is busy |
| Memory/crash on Pi | Increase swap in Pi config, disable animations in config.py |

## Questions?

Check the console output first—it's designed to tell you exactly what's wrong.

Good luck! 🎨
