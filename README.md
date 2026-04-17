# NukeCodeBridge
**NukeCodeBridge v0.5 beta**

A simple tool that lets you save, organize, and run Python scripts directly inside Nuke using a shared network folder. No more copying scripts around — everyone in the studio can access the same tools easily.

## ✨ Features
* Save scripts to a shared location (one folder per user by default)
* Built-in code editor with line numbers, syntax highlighting, and auto-indent
* Run scripts directly from the editor
* Search and right-click menu (Run, Rename, Delete, Copy path)
* **Dev-Friendly:** Automatically reloads code changes without restarting Nuke
* Works on Windows and Linux (Nuke 13+)

## 🚀 Easy Installation

### Step 1: Prepare the folders
1. Choose a **scripts folder** on the network where the `.py` files will live (e.g., `\\server\share\SharedNukeScripts`).
2. Place the file **nuke_code_bridge.py** in your Nuke plugin path (e.g., `\\server\share\pipelinetools`).

### Step 2: Update init.py
Add this to your `init.py`. It tells Nuke where to look for the tool. We use `print` instead of `nuke.message` to ensure render nodes don't hang if the path is missing.

```python
import nuke
import os

# Path to the folder containing nuke_code_bridge.py
BRIDGE_PATH = r"Y:\dev_remco\pipelinetools"

if os.path.exists(BRIDGE_PATH):
    nuke.pluginAddPath(BRIDGE_PATH)
else:
    print(f"NukeCodeBridge path not found: {BRIDGE_PATH}")
```

### Step 3: Update menu.py
Add this to your `menu.py`. This version includes `importlib`, which allows you to update the tool's code and see changes immediately by just re-opening the window.

```python
import nuke
import importlib

def launch_bridge():
    try:
        import nuke_code_bridge
        importlib.reload(nuke_code_bridge)
        nuke_code_bridge.start_nuke_code_bridge()
    except Exception as e:
        nuke.message(f"Failed to load NukeCodeBridge:\n{str(e)}")

nuke.menu('Nuke').addCommand(
    'Scripts/NukeCodeBridge', 
    launch_bridge, 
    tooltip='Open NukeCodeBridge - Network Script Manager'
)
```

## ⚙️ How to Configure
Configuration is handled at the top of **nuke_code_bridge.py**:

```python
# 1. Set your studio network location (Where scripts are SAVED)
BASE_SHARED_PATH = r"\\server\share\SharedNukeScripts"

# 2. Safety Toggle
SHOW_RUN_CONFIRMATION = True

# 3. Folder Mode
# False: Users get private folders (UserA, UserB)
# True: Everyone saves to one "Shared" folder
USE_SINGLE_SHARED_FOLDER = False
```

## Requirements
* Nuke 13 or newer (Supports PySide2 and PySide6)
* Read/write access to the network scripts folder

## Notes & Security
* **Singleton UI:** The updated script now prevents multiple windows from opening simultaneously.
* **Security:** Only run code from trusted sources. A confirmation popup is enabled by default.
* **Troubleshooting:** If the menu fails, check the Nuke terminal for "path not found" errors during startup.
