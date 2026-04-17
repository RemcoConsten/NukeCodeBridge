# NukeCodeBridge
**NukeCodeBridge v0.5 beta**
A simple tool that lets you save, organize, and run Python scripts directly inside Nuke using a shared network folder.
No more copying scripts around — everyone in the studio can access the same tools easily.
## ✨ Features
 * Save scripts to a shared location (one folder per user by default)
 * Built-in code editor with line numbers, syntax highlighting, and auto-indent
 * Run scripts or just selected parts of code
 * Search and right-click menu (Run, Rename, Delete, Copy path)
 * Works on both Windows and Linux
 * Supports Nuke 13 and newer versions
## 🚀 Easy Installation (Step-by-step)
### Step 1: Prepare the folders
 1. Create (or choose) your main **scripts folder** on the network. This is where all the Python scripts will be saved.
   Example: \\server\share\SharedNukeScripts
   **If you are working alone or in a small studio**, you can create this on your local drive (e.g. C:\NukeScripts).
   **Tip:** Use full network paths like \\server\share\... instead of mapped drive letters like Y:\ — this works better on all computers.
 2. Place the file **nuke_code_bridge.py** in a folder that Nuke can access (for example, a tools folder).
### Step 2: Update init.py
Open or create the studio’s init.py file and add the path to the folder containing nuke_code_bridge.py. This allows Nuke to find the tool on startup:
```python
import nuke
import os

# Path to the folder containing nuke_code_bridge.py
NUKE_CODE_BRIDGE_PATH = r"\\YOUR_SERVER\YOUR_SHARE\tools"

if os.path.exists(NUKE_CODE_BRIDGE_PATH):
    nuke.pluginAddPath(NUKE_CODE_BRIDGE_PATH)
else:
    nuke.message(f"Warning: NukeCodeBridge path not found:\n{NUKE_CODE_BRIDGE_PATH}")

```
### Step 3: Update menu.py
Open or create the studio’s menu.py file and add this code to create the menu entry:
```python
import nuke

def launch_nuke_code_bridge():
    """Launch NukeCodeBridge v0.5 beta"""
    try:
        import nuke_code_bridge
        nuke_code_bridge.start_nuke_code_bridge()
    except Exception as e:
        nuke.message(f"Failed to load NukeCodeBridge:\n{str(e)}")

nuke.menu('Nuke').addCommand(
    'Scripts/NukeCodeBridge', 
    launch_nuke_code_bridge,
    tooltip='Open NukeCodeBridge - Network Script Manager'
)

```
## ⚙️ How to Configure
All settings are managed inside **nuke_code_bridge.py**. Open it in a text editor to adjust the following at the top of the script:
```python
# 1. Set your studio network location
BASE_SHARED_PATH = r"\\YOUR_SERVER\YOUR_SHARE\SharedNukeScripts"

# 2. Safety Toggle
# Set to True (default) to show a confirmation popup before running code.
SHOW_RUN_CONFIRMATION = True

# 3. Folder Mode
# Set to True to use one common folder for all users (no per-user subfolders)
USE_SINGLE_SHARED_FOLDER = False

```
### Folder Modes:
 * **Per-User Folders** (False - default): Each user gets their own subfolder within the main path.
 * **Single Shared Folder** (True): Everyone uses a single folder named "Shared".
## Requirements
 * Nuke 13 or newer
 * Read/write access to the scripts folder
 * No extra software needed
## Notes & Security
 * This is an early version (v0.5). Feel free to try it out and report any issues.
 * **Security**: Only run scripts from people you trust.
 * A confirmation popup is enabled by default before running any code.
 * Make sure your team has read/write access to the shared network folder.
