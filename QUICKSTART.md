# Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Install Python Dependencies (1 min)
```bash
cd c:\Users\Rodi\Desktop\GrandMa3MitComputerVision

# Aktiviere das Virtual Environment
.\venv\Scripts\Activate.ps1

# Installiere Dependencies (bereits erledigt!)
pip install -r requirements.txt
```

### Step 2: Configure grandMA3 (2 min)

1. **Enable OSC Input:**
   - `Menu → In & Out → OSC`
   - Enable OSC Input, Port: `8000`

2. **Create User Variables:**
   - `Menu → Show → User Variables`
   - Add: `TrackingX` (Float, 0-100)
   - Add: `TrackingY` (Float, 0-100)

3. **Map OSC to Variables:**
   - `Menu → In & Out → OSC → Input Configuration`
   - `/stage/person1/x` → `$TrackingX` (0.0-1.0 → 0-100)
   - `/stage/person1/y` → `$TrackingY` (0.0-1.0 → 0-100)

### Step 3: Install Lua Plugin (1 min)

Copy `TrackingPlugin.lua` to your MA3 plugins folder:
- **Windows:** `C:\ProgramData\MALightingTechnology\gma3_X.X.X\plugins\`
- **macOS:** `~/MALightingTechnology/gma3_X.X.X/plugins/`

### Step 4: Run! (1 min)

1. **Start Python tracker:**
   ```bash
   # Aktiviere venv (falls noch nicht aktiv)
   .\venv\Scripts\Activate.ps1
   
   # Starte Tracker
   python person_tracker_osc.py --ip <YOUR_MA3_IP>
   ```
   
2. **Start MA3 plugin:**
   - `Menu → Plugins → TrackingPlugin`

3. **Stand in front of camera** - the fixture should follow you!

---

## 📝 Configuration Checklist

Before first run, configure these values:

### In TrackingPlugin.lua
```lua
FIXTURE_ID = 101,        -- ← Change to your fixture ID
PAN_MAX = 540,           -- ← Adjust to your fixture's pan range
TILT_MAX = 270,          -- ← Adjust to your fixture's tilt range
```

### When running Python script
```bash
python person_tracker_osc.py --ip 127.0.0.1
python person_tracker_osc.py --ip 192.168.1.100  # ← Your MA3 IP
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Camera won't open | Try `--camera 1` or check if another app is using it |
| No OSC connection | Check IP address and firewall settings |
| Fixture not moving | Verify fixture ID and ensure it has intensity |
| Jerky movement | Increase `SMOOTHING` to 0.3-0.5 in Lua plugin |

For detailed help, see [README.md](file:///c:/Users/Rodi/Desktop/GrandMa3MitComputerVision/README.md)
