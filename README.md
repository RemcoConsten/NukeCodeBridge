# NukeCodeBridge
**v0.5 beta | Network-Based Script Manager for Foundry Nuke**

NukeCodeBridge is a lightweight pipeline tool designed for VFX studios and teams. It allows artists to save, share, and execute Python snippets directly within Nuke via a centralized network location, eliminating the need to manually share `.py` files or copy-paste code through chat apps.

## ✨ Features
* **Shared Repository:** Centralized storage for team-wide or personal scripts.
* **Smart Editor:** Integrated editor with Python syntax highlighting, line numbers, and auto-indentation.
* **User Isolation:** Supports both "Per-User" subfolders and "Single Shared" folder modes.
* **Dev-Friendly:** Built-in module reloading—apply code changes instantly without restarting Nuke.
* **Safety First:** Optional execution confirmation to prevent accidental script runs.
* **Cross-Platform:** Compatible with Windows and Linux (Nuke 13.0+).

---

## 🚀 Installation

### 1. Deployment
Place `nuke_code_bridge.py` into a shared studio directory or your local Nuke plugin path.

### 2. Environment Setup (`init.py`)
Add the directory containing the script to your Nuke plugin path. Add the following to your `init.py`:

```python
import os
import nuke

# Replace with the path where you placed nuke_code_bridge.py
TOOL_PATH = r"\\YOUR_SERVER\path\to\tool"

if os.path.exists(TOOL_PATH):
    nuke.pluginAddPath(TOOL_PATH)
else:
    print(f"[NukeCodeBridge] Warning: Tool path not found: {TOOL_PATH}")
```

### 3. Menu Integration (`menu.py`)
Add the launcher command to your `menu.py`:

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

nuke.menu('Nuke').addCommand('Scripts/NukeCodeBridge', launch_bridge)
```

---

### ⚠️ Pre-launch Configuration
Before attempting to run the bridge, you **must** configure the script settings. Without defining your network paths, the bridge will fail to initialize.

Open `nuke_code_bridge.py` in your preferred text editor and update the following variables at the top of the file:

| Variable | Description |
| :--- | :--- |
| **`BASE_SHARED_PATH`** | The absolute network path where scripts that you would like to share with everyone are stored. Ensure all users have read/write permissions here. |
| **`SHOW_RUN_CONFIRMATION`** | Set to `True` to show an "Are you sure?" popup before execution; `False` for instant execution. |
| **`USE_SINGLE_SHARED_FOLDER`** | If `False`, users get private subfolders based on their username. If `True`, all users share a global folder. |

---

### Implementation Pro-Tip
To make this even more user-friendly, you might consider adding a simple check at the start of your `main()` function:

```python
if BASE_SHARED_PATH == "/path/to/your/network/share":
    nuke.critical("Bridge Error: Please configure BASE_SHARED_PATH in nuke_code_bridge.py")
    return
```

This prevents the script from silently failing and gives the user a clear nudge to go back to the config. 

Does this flow better with the rest of your documentation, or should we add a "Quick Start" checklist at the very top?

---

## 🛠 Requirements
* **Foundry Nuke:** 13.0 or newer.
* **Python:** 3.7+ (Standard with Nuke 13+).
* **Permissions:** Read/Write access to the `BASE_SHARED_PATH`.

## 🔒 Security & Usage
* **Trust:** Only execute scripts from trusted team members.
* **Permissions:** Ensure the shared network directory has the correct Read/Write permissions for your user group.
* **Beta Software:** This tool is currently in beta. Always back up critical scripts.

---

## 🤝 Contributing
Contributions are welcome! Feel free to submit Pull Requests or open Issues to suggest new features or report bugs.
