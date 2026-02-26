# DEPLOY_TO_PI.md

# Deploying Synthetic Relic to Raspberry Pi

Once you've tested on Mac and are happy with the logic, deploying to the Pi is straightforward.

## Hardware Setup

### Required
- Raspberry Pi 4 (8GB recommended) or Pi 5
- 10" touchscreen display (e.g., official Pi Display, Elecrow 10.1")
- USB microphone (or 3.5mm mic + adapter)
- Power supply (USB-C for Pi 5, Micro-USB for Pi 4)
- 32GB+ microSD card (Pi OS)

### Optional
- Small speaker for feedback sounds
- Case/stand for portability
- Ethernet cable (faster than WiFi initially)

## Software Setup

### 1. Install Raspberry Pi OS

Use Raspberry Pi Imager:
- Download from https://www.raspberrypi.com/software/
- Flash to microSD card
- Choose "Raspberry Pi OS Lite" (headless) or full desktop version
- Enable SSH and set password during flashing

### 2. Boot and Connect

```bash
# SSH into Pi (from your Mac)
ssh pi@raspberrypi.local
# Default password: raspberry
```

Update system:
```bash
sudo apt update
sudo apt upgrade -y
```

### 3. Install Dependencies

```bash
# Python and pip
sudo apt install -y python3-pip python3-venv

# OpenCV dependencies
sudo apt install -y libatlas-base-dev libjasper-dev libtiff5 libjasper1 libharfft0 libwebp6 libtiff5 libjasper1 libharfft0 libwebp6 libopenjp2-7 libtiff5

# Audio/voice libraries
sudo apt install -y portaudio19-dev

# Git (to clone your repo)
sudo apt install -y git
```

### 4. Clone Your Project

```bash
git clone https://github.com/yourusername/synthetic-relic.git
cd synthetic-relic
```

### 5. Set Up Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

This will take a few minutes on Pi.

### 6. Set API Token

Add to `~/.bashrc`:

```bash
echo 'export REPLICATE_API_TOKEN="your_token_here"' >> ~/.bashrc
source ~/.bashrc
```

### 7. Configure for Touchscreen

Edit `config.py`:

```python
# For 10" display, common resolutions:
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

# Or fill the screen:
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
```

For the official Pi touchscreen (7" or 10"), you may need to configure display orientation and rotation. Check Raspberry Pi docs.

### 8. Test on Pi

```bash
python3 main.py
```

Try a full cycle. Check that:
- Drawing canvas appears and is touchscreen-responsive
- Voice input works
- API calls succeed
- Animation plays smoothly
- Gallery saves

### 9. Auto-Start on Boot (Optional)

Create a systemd service so the installation runs when Pi boots:

```bash
sudo nano /etc/systemd/system/synthetic-relic.service
```

Paste:

```ini
[Unit]
Description=Synthetic Relic Installation
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=10
User=pi
WorkingDirectory=/home/pi/synthetic-relic
Environment="REPLICATE_API_TOKEN=your_token_here"
ExecStart=/home/pi/synthetic-relic/venv/bin/python3 /home/pi/synthetic-relic/main.py

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable synthetic-relic
sudo systemctl start synthetic-relic

# Check status
sudo systemctl status synthetic-relic

# View logs
sudo journalctl -u synthetic-relic -f
```

### 10. Performance Tuning

The Pi may run slower than your Mac. Adjustments:

In `config.py`:

```python
# Reduce quality for faster generation
REPLICATE_MODEL = "..."  # Use a lighter model if available

# Shorten animations to reduce CPU load
ANIMATION_DURATION = 5
GALLERY_DISPLAY_DURATION = 3

# Reduce drawing/voice durations
DRAWING_DURATION = 10
VOICE_DURATION = 8

# Disable some effects
ENABLE_MORPHING = False
ENABLE_FADE_IN = False
```

### 11. Storage Management

The gallery directory grows over time. Configure cleanup:

In `config.py`:

```python
MAX_GALLERY_AGE_HOURS = 24   # Delete entries > 24 hours old
MAX_GALLERY_ENTRIES = 50     # Keep only 50 most recent
```

Monitor disk usage:

```bash
df -h
du -sh ~/synthetic-relic/gallery/
```

### 12. Network Considerations

**WiFi**: Fine for most use cases. Add network auto-reconnect in `main.py` if installing in spotty WiFi:

```python
# Add at top of main loop
def ensure_internet():
    try:
        requests.get("https://api.replicate.com", timeout=5)
    except:
        logger.warning("No internet, waiting...")
        time.sleep(10)
```

**Offline mode**: To work without internet, modify `config.py`:

```python
ENABLE_API = False
MOCK_API_RESPONSE = True
```

This uses procedural/mock images instead of Replicate.

## Troubleshooting on Pi

### "Permission denied" on /dev/ttyACM0

USB device permissions. Run:

```bash
sudo usermod -a -G dialout pi
sudo usermod -a -G audio pi
```

Then log out and back in.

### Audio not working

Check devices:

```bash
arecord -l
aplay -l
```

Set default device in `~/.asoundrc` if needed.

### Touchscreen not responding

Update the kernel and check display drivers:

```bash
sudo apt install -y raspberrypi-kernel
sudo rpi-update
```

Reboot and test.

### Slow API response / timeouts

The Pi's internet may be slower. Increase timeout in `core/api_client.py`:

```python
self.timeout = 180  # 3 minutes instead of 2
```

### Out of memory / crashes

Increase swap:

```bash
sudo nano /etc/dphys-swapfile
# Change CONF_SWAPSIZE=100 to CONF_SWAPSIZE=2048
sudo /etc/init.d/dphys-swapfile restart
```

## Portable Deployment

For moving the installation between venues:

1. **Create a backup image** (if you want to clone setup):
   ```bash
   # On Mac, from another machine
   sudo dd if=/dev/disk2 of=synthetic-relic.img bs=4m
   # Then burn to new microSD with Balena Etcher
   ```

2. **Minimal dependencies**: Use the Pi Lite OS (command-line only) to reduce size and startup time.

3. **Portable power**: Use a UPS or large USB power bank for brief power loss tolerance.

4. **Network resilience**: Test WiFi at installation venue beforehand. Bring an Ethernet adapter if available.

## Next: Physical Enclosure

Once software is stable:

1. Mount Pi + screen in a pedestal (see original concept)
2. Hide microphone and camera (if adding later)
3. Route power through the base
4. Add a cooling solution (fan or passive heatsink) if running 8+ hours continuously

## Monitoring

Check Pi health:

```bash
vcgencmd measure_temp          # CPU temperature
free -h                         # Memory usage
df -h                           # Disk usage
uptime                          # How long since boot
```

Set up log monitoring to catch crashes:

```bash
sudo journalctl -u synthetic-relic -f
```

## Going Live

Before placing in public:

- [ ] Test full 8-hour continuous operation
- [ ] Verify API token has enough credits
- [ ] Test with multiple users (rapid interactions)
- [ ] Check thermal performance (no overheating)
- [ ] Verify network connectivity at venue
- [ ] Set up crash recovery (systemd auto-restart)
- [ ] Create a "reset" procedure if installation hangs
- [ ] Backup gallery before moving locations

Good luck! 🚀
