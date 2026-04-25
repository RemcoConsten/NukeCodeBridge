# NukeCodeBridge v0.15

![Version](https://img.shields.io/badge/version-v0.15-green)
![License](https://img.shields.io/badge/license-MIT-blue)
![OS-Windows](https://img.shields.io/badge/Windows-Tested-green)
![OS-macOS](https://img.shields.io/badge/macOS-Experimental-yellow)
![OS-Linux](https://img.shields.io/badge/Linux-Experimental-yellow)
![Nuke](https://img.shields.io/badge/Nuke-13.0+-green)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)
![Stars](https://img.shields.io/github/stars/RemcoConsten/NukeCodeBridge?style=social)

<img width="601" height="416" alt="image" src="https://github.com/user-attachments/assets/a504487e-73f1-4100-be0d-5c1caeedbad9" />
<br>
**Network-Based Script Manager & Python Editor for Foundry Nuke**

NukeCodeBridge is a lightweight, production-oriented tool for VFX studios, teams, and solo artists.
It allows you to **store, edit, run, and share Python scripts directly inside Nuke** using a shared network repository - no more Slack-shared `.py` files or digging through old scripts.

---

## How I Built This: An Artist's Perspective

I am an artist, not a full-time developer. Like many people in production, I often have ideas for tools that could make our lives easier, and while I know how to move around within Python, I often hit that coding wall.

This tool was an experiment to see if I could use AI as a technical assistant to bring a creative idea to life. And yes, I also used AI to help me write this README to save time. Some of you might find that lazy; I'm starting to find it a way to spend my precious time on something else.

**The Director Workflow:** Instead of writing every line of code from scratch, I acted more like a director.
**The Concept:** I knew I wanted a way to share Nuke code snippets quickly across the studio without digging through folders.
**The AI Collaboration:** I used AI to do the heavy lifting of building the interface. I described how I wanted the UI to react and how the list should behave, and the AI provided the building blocks.
**Problem Solving:** When things broke, I worked with the AI to troubleshoot, testing different versions until it worked perfectly inside the Nuke environment.
**Why I'm Sharing This:** I wanted to be open about using AI because I think it's a game-changer for artists. It allows those of us who speak VFX but maybe do not speak Python fluently to build professional-grade tools.

---

## ⚡ Quick Start

1. Drop `nuke_code_bridge.py` into your `.nuke` folder
2. Add the launcher to your `menu.py` (see [Installation](#installation))
3. Set `BASE_SHARED_PATH` at the top of the tool file to a folder you have read/write access to
4. Launch Nuke → **Scripts > NukeCodeBridge**

---

## 🔧 Installation

There are **two completely separate paths** to understand before you start:

| | Path | What it is for |
|---|---|---|
| **Tool file** | Where `nuke_code_bridge.py` lives | So Nuke can import and launch the tool |
| **Shared data** | `BASE_SHARED_PATH` inside the tool | Where scripts, snippets, and comments are stored |

These can be the same folder, but in most studio setups the tool lives in a pipeline tools folder and the data lives in a separate shared folder.

---

### Step 1: Place the tool file

**Option A — Solo artist / simplest setup**

Drop `nuke_code_bridge.py` directly into your `.nuke` folder:

```
C:\Users\yourname\.nuke\nuke_code_bridge.py
```

Nuke loads everything in the `.nuke` folder automatically. You do **not** need an `init.py` for this option — skip straight to Step 2.

**Option B — Studio / shared pipeline**

Place the file in a shared tools folder on your server:

```
\\YOUR_SERVER\YOUR_SHARE\pipeline\tools\nuke_code_bridge.py
```

Then add this to your `init.py` so Nuke knows where to find it:

```python
import os
import nuke

# Option A: set NUKE_CODE_BRIDGE_PATH as a system environment variable on each workstation
# Option B: replace the fallback string below with the actual path on your server
TOOL_PATH = os.environ.get(
    "NUKE_CODE_BRIDGE_PATH",
    r"\\YOUR_SERVER\YOUR_SHARE\pipeline\tools"   # <-- folder containing nuke_code_bridge.py
)

if os.path.exists(TOOL_PATH):
    nuke.pluginAddPath(TOOL_PATH)
else:
    print(f"[NukeCodeBridge] Warning: Tool path not found: {TOOL_PATH}")
```

---

### Step 2: Set up menu.py

**This step is required for both Option A and Option B.**

Add this to your `menu.py` to get the NukeCodeBridge entry in the Nuke menu.
`importlib.reload` means updates to the tool apply the next time you open it — no Nuke restart needed:

```python
import nuke
import importlib

def launch_nuke_code_bridge():
    try:
        import nuke_code_bridge
        importlib.reload(nuke_code_bridge)
        nuke_code_bridge.start_nuke_code_bridge()
    except Exception as e:
        nuke.message(f"Failed to load NukeCodeBridge:\n{str(e)}")

nuke.menu('Nuke').addCommand(
    'Scripts/NukeCodeBridge',
    launch_nuke_code_bridge,
    icon='',       # Optional: place a .png in the same folder and set the filename here
    tooltip='Network-based Python script manager for studio teams.'
)
```

> **Where is menu.py?**
> For Option A (solo), this is `C:\Users\yourname\.nuke\menu.py` — the same folder as the tool file.
> For Option B (studio), this is your studio's shared `menu.py`, already loaded by Nuke via `init.py`.

---

### Step 3: Set BASE_SHARED_PATH inside the tool

Open `nuke_code_bridge.py` and set this at the top:

```python
BASE_SHARED_PATH = r"\\YOUR_SERVER\YOUR_SHARE\pipeline\NukeCodeBridge"
```

This is the shared folder where all user script folders, snippets, and comments will be stored.
Every user on the team needs read/write access to this location.

> **Solo artist?** This can be any local folder on your machine:
> ```python
> BASE_SHARED_PATH = r"C:\Users\yourname\Documents\NukeCodeBridge"
> ```

---

## ⚙️ Configuration

All settings are at the top of `nuke_code_bridge.py`:

```python
BASE_SHARED_PATH          = r"\\YOUR_SERVER\YOUR_SHARE\pipeline\NukeCodeBridge"
SHOW_RUN_CONFIRMATION     = True    # ask before running code
USE_SINGLE_SHARED_FOLDER  = False   # True = everyone shares one folder
ENABLE_BACKUPS            = True
MAX_BACKUPS               = 3       # how many .bak versions to keep
MAX_HISTORY_ITEMS         = 25
CONFIRM_OVERWRITE         = False   # True = ask before overwriting on save
AUTOSAVE_INTERVAL_MINUTES = 5       # crash recovery interval (0 = disabled)
```

---

## 🎬 Usage

1. Open Nuke
2. Go to **Scripts > NukeCodeBridge**
3. Select a script from the sidebar or start with a new Untitled tab
4. Edit your Python or Blink code
5. Save with Ctrl+S — first save: enter a filename in the top bar first
6. Run with Ctrl+Enter
7. View output in the console below

---

## 📁 Folder Structure

```
BASE_SHARED_PATH/
  shared_snippets.json            <- team-wide snippets
  username/
    username_snippets.json        <- personal snippets
    .session_recovery.json        <- untitled tab restore
    scripts/
      myscript.py
      _backups/
        myscript/
          20240101_120000.bak
      _meta/
        myscript.meta.json        <- description + comments + read timestamps
        myscript.meta.lock        <- concurrent write protection
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| Ctrl+S | Save |
| Ctrl+Enter | Run entire script |
| Ctrl+Shift+Enter | Run selected text |
| Ctrl+F | Open Find & Replace |
| Ctrl+G | Go to line |
| Ctrl+Shift+T | Reopen last closed tab |
| Esc | Close Find bar |
| Ctrl+Mouse Wheel | Zoom editor |
| Ctrl+0 | Reset zoom |
| Tab | Indent selection or expand snippet |
| Shift+Tab | Unindent |

---

## 🧰 Features (v0.15)

| | Category | What it does |
|---|---|---|
| 🌐 | **Network Repository** | Per-user script folders on a shared path. Toggle between your folder and `all_users`. Right-click to open location or delete. New scripts go into `username/scripts/`, legacy scripts still show up. |
| 📑 | **Multi-Tab Editor** | Unlimited tabs with dirty state tracking (`*`), session restore for untitled tabs, duplicate tab, and Ctrl+Shift+T to reopen last closed. |
| ✏️ | **VS Code-Style Editing** | Dark+ syntax highlighting, line numbers, current line highlight, word-occurrence highlight, indent guides, no line wrapping. Zoom with Ctrl+Wheel or Ctrl+plus/minus/0. |
| 🔍 | **Search** | Sidebar toggles between Name mode (filter by filename) and Contents mode (search inside all files). Find & Replace with Prev/Next/Replace All and wrap-around. |
| ⚡ | **Snippet System** | Type a trigger word and press Tab to expand. Amber highlight with 150ms debounce. `$CURSOR$` marks where the cursor lands. Three pools: Built-in (read-only), Shared (team), Personal (yours). Full Snippet Manager with create, edit, delete, move to shared, insert into editor. |
| 💬 | **Script Info & Comments** | Per-script description and team comments stored in `_meta/`. Unread tracking shows `+N` on the collapsed header. Lock file prevents write conflicts. Last 50 comments per script kept. |
| 🎛️ | **knobChanged Editing** | Select node(s) in the graph and click Edit knobChanged — each opens in its own tab. Falls back to Node Picker if nothing is selected. Save writes back to the node knob. If the node is deleted, Save As keeps your code as a file. |
| 🎯 | **Node Picker** | Browse and filter all scene nodes. Pick button starts a 5s countdown — click any new node in the graph to grab it. Pre-existing selections are ignored. Click again to cancel. |
| ▶️ | **Run Options** | Run entire script, run selection only, or wrap in a for-loop over selected nodes (`node` variable available). Send to Nuke Script Editor pushes code to Nuke's built-in panel. |
| 💾 | **Save, Backups & Crash Recovery** | Binary-hardened saving. Timestamped `.bak` files on every save, last 3 versions kept. Silent `.autosave` every 5 minutes for dirty tabs — right-click the `⚠` tab to restore or discard. |
| 🖥️ | **Execution & Console** | Persistent namespace between runs. Full traceback capture. Status light (idle / running / success / error). Console filter by All / Errors Only / Actions+Info. Execution history with double-click restore. Variable explorer. All sidebar panels collapsible. |

**Built-in snippet triggers:**

| Trigger | Expands to |
|---|---|
| `fornode` | `for node in nuke.selectedNodes():` |
| `ifnuke` | `if nuke:` |
| `tryex` | try/except block |
| `defn` | function definition |
| `blink` | Blink kernel template |
| `blinkp` | Blink param block |

---

## 🆕 What's New Since v0.12

### v0.15
- **Snippet system** - trigger words with amber highlight, Tab to expand, `$CURSOR$` placeholder
- **Snippet Manager** - personal, shared, and built-in pools with full CRUD
- **Script Info & Comments** - per-script description and team comments, stored in `_meta/` folder
- **Unread comment tracking** - header shows `+N` for unread comments from teammates
- **Smart knobChanged editing** - select node(s) in graph, click Edit knobChanged; falls back to Node Picker if nothing selected
- **Node Picker** - browse/filter all scene nodes, with Pick button (5s countdown, ignores pre-existing selection)
- **Name/Contents search toggle** - filter list by name or search inside all files live
- **Session restore** - untitled tabs with content survive close/reopen
- **Crash recovery autosave** - silent `⚠` tab indicator, right-click to restore or discard
- **scripts/ subfolder** - new scripts save to `username/scripts/`, legacy scripts still show up
- **Collapsible sidebar panels** - Node Picker, History, Variables, Script Info all collapse/expand
- **Find & Replace bar** - Ctrl+F with Prev/Next/Replace/Replace All
- **Go to Line** - Ctrl+G
- **Reopen last closed tab** - Ctrl+Shift+T
- **Run on Selected Nodes** - wraps script in for-node loop
- **Send to Nuke Script Editor** - pushes code to Nuke's built-in panel
- **Manual tab** - full reference built into the tool
- Compatible with **Nuke 15 and 17** (PySide2 + PySide6)

### v0.12
- Full VS Code Dark+ themed editor
- Multi-tab editing
- Line numbers with custom gutter
- Current line highlight + word-occurrence highlighting
- Zoom system (Ctrl+Wheel, Ctrl+plus/minus, Ctrl+0)
- Indent/unindent (Tab / Shift+Tab)
- Improved syntax highlighting
- Status light (idle / running / success / error)
- Dark-themed console output
- Safer save and backup behavior

### v0.11
- Modular refactor
- Initial multi-tab structure
- Improved repository handling
- Basic save + backup system
- Console redirection
- Persistent namespace

### v0.9
- First public beta
- Single-tab editor
- Basic network loading
- Basic execution

---

## 🗺️ Roadmap

<sub>See the full roadmap in [ROADMAP.md](ROADMAP.md)</sub>
---

## 📋 Requirements

- **Foundry Nuke:** 13.0 or newer (Tested on Nuke 15 and 17)
- **Python:** 3.7+ (Standard with Nuke 13+)
- **Permissions:** Read/Write access to `BASE_SHARED_PATH` for all users

---

## 🔒 Security & Usage

- **Trust:** Only execute scripts from trusted team members.
- **Caution:** This tool uses Python's `exec()` - just like Nuke's Script Editor.
  Executing unverified code can cause crashes or data loss.
- **Permissions:** Ensure the shared directory has correct read/write access for all users.
- **Beta Software:** Always back up critical scripts before running them.

---

## 🤝 Contributing

Contributions, discussions, and ideas are welcome!
Submit Pull Requests or open Issues - especially if you are testing on Linux or macOS.

---

## Created by Remco Consten
VFX Artist & Pipeline Enthusiast
<a href="https://www.linkedin.com/in/remcoconsten/" target="_blank">LinkedIn</a>

---
