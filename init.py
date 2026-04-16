import nuke
import os

# =============================================
# NukeCodeBridge v0.5 beta — Remco Consten
# Network Script Manager for Nuke
# =============================================

# <<< EDIT THIS PATH TO WHERE YOUR NukeCodeBridge.py IS LOCATED >>>
# This tells Nuke where to find the tool on startup.

# Example paths:
# Windows: r"\\server\share\tools"   or   r"Y:\StudioTools"
# Linux:   "/mnt/studio/tools"

NUKE_CODE_BRIDGE_PATH = r"\\YOUR_SERVER\YOUR_SHARE\tools"   # ← CHANGE THIS

# Add the directory containing NukeCodeBridge.py to Nuke's plugin path
if os.path.exists(NUKE_CODE_BRIDGE_PATH):
    nuke.pluginAddPath(NUKE_CODE_BRIDGE_PATH)
    # Optional quiet confirmation (uncomment if you want to see it once)
    # print("NukeCodeBridge v0.5 beta — Path added successfully")
else:
    nuke.message(f"Warning: NukeCodeBridge path not found:\n{NUKE_CODE_BRIDGE_PATH}")

# =============================================
