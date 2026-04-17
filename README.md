# NukeCodeBridge
![Version](https://img.shields.io/badge/version-v0.9--beta-orange)
![License](https://img.shields.io/badge/license-MIT-blue)
![OS-Windows](https://img.shields.io/badge/Windows-Tested-green)
![OS-macOS](https://img.shields.io/badge/macOS-Experimental-yellow)
![OS-Linux](https://img.shields.io/badge/Linux-Experimental-yellow)
![Nuke](https://img.shields.io/badge/Nuke-13.0+-green)

**v0.9 beta | Network-Based Script Manager for Foundry Nuke**

NukeCodeBridge is a lightweight pipeline tool designed for VFX studios and teams or solo artists. It allows artists to save, share, and execute Python snippets directly within Nuke via a centralized network location, eliminating the need to manually share `.py` files or copy-paste code through chat apps.

<img width="551" height="380" alt="image" src="https://github.com/user-attachments/assets/bbf6d4ab-60d0-41ea-a6cf-315566b06fe1" />

---

* **How I Built This With The Help Of AI: From an Artists Perspective:** ​I am an artist, not a fulltime developer. Like many people in production, I often have ideas for tools that could make our lives easier, and while I know how to move around within python, I ofter hit that coding wall.

​This tool was an experiment to see if I could use AI as a technical assistant to bring a creative idea to life. And yes, I also used AI to helped me write this Readme to save time. Some of you might find that lazy. lm starting to find it a way to spend my precious time on something else.

* **The Director Workflow:** Instead of writing every line of code from scratch, I acted more like a director.
​The Concept: I knew I wanted a way to share Nuke code snippets quickly across the studio without digging through folders.

* **​The AI Collaboration:** I used AI to do the heavy lifting of building the interface. I described how I wanted UI to react and how the list should behave, and the AI provided the building blocks.
  
* **​Problem Solving:** When things broke I worked with the AI to troubleshoot, testing different versions until it worked inside the Nuke environment.

* **Why I’m Sharing This:** ​I wanted to be open about using AI because I think it’s a game changer for artists. It allows those of us who speak VFX but maybe do not speak Python fluently to build professional grade tools.

---

## ✨ Features

**Script Management**
* **Multi-User Repositories:** Access and load scripts from various user directories across the network.
* **Search and Filter:** Real-time text filtering to locate specific scripts within the active folder.
* **Context Menu:** Right-click functionality to open the file location in the operating system or delete scripts with a confirmation prompt.
* **Status Bar:** Bottom-aligned interface showing the current repository name and total file count.

**Editor Interface**
* **Line Numbering:** Dedicated margin displaying current line counts.
* **Syntax Highlighting:** Color-coded recognition for Python keywords, strings, and comments.
* **Active Line Tracking:** Visual highlighting of the line currently containing the cursor.
* **UTF-8 Support:** Full encoding support for Unicode characters, preventing save/load errors with special symbols.
* **Monospaced Typography:** Fixed-pitch font selection to ensure accurate indentation and alignment.

**Integration and Stability**
* **Stay-on-Top Behavior:** Window flags set to keep the tool visible over the Nuke interface.
* **Parented Dialogs:** Custom logic ensuring confirmation and error messages appear in front of the main UI.
* **Adjustable Layout:** Integrated splitter allowing users to resize the browser and editor panels.
* **Multi-Version Support:** Compatible with both PySide2 and PySide6 for different Nuke versions.
* **Execution Safety:** Optional confirmation toggle before running code in the global context.
* **tested on windows** I tested the tool on Windows, but it should be compatible with Linux as well. Unfortunately I'm not able to test this right now. 
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

## 🛠 Requirements
* **Foundry Nuke:** 13.0 or newer. (tested on nuke 15) 
* **Python:** 3.7+ (Standard with Nuke 13+).
* **Permissions:** Read/Write access to the `BASE_SHARED_PATH`.

## 🔒 Security & Usage
* **Trust:** Only execute scripts from trusted team members.
*  **Caution:** This tool uses Python's exec() function. Just like the native Nuke Script Editor, executing unverified code can lead to data loss, software crashes, or unintended system changes.
* **Permissions:** Ensure the shared network directory has the correct Read/Write permissions for your user group.
* **Beta Software:** This tool is currently in beta. Always back up critical scripts.

---

## 🤝 Contributing
Contributions, discussions and ideas are welcome! Feel free to submit Pull Requests or open Issues to suggest new features or report bugs.

---

### 👨‍💻 Created by Remco Consten
*VFX Artist & Pipeline Enthusiast*---

[🔗 LinkedIn] (https://nl.linkedin.com/in/remco-consten-18449626&ved=2ahUKEwja_LOC9fWTAxW32gIHHdEAHKMQFnoECBoQAQ&usg=AOvVaw2ToeYLqTqA3Yd9z1TBSc-d) 
