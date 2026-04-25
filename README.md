# NukeCodeBridge

![Version](https://img.shields.io/badge/version-v0.15-green)
![License](https://img.shields.io/badge/license-MIT-blue)
![OS-Windows](https://img.shields.io/badge/Windows-Tested-green)
![OS-macOS](https://img.shields.io/badge/macOS-Experimental-yellow)
![OS-Linux](https://img.shields.io/badge/Linux-Experimental-yellow)
![Nuke](https://img.shields.io/badge/Nuke-13.0+-green)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)
![Stars](https://img.shields.io/github/stars/RemcoConsten/NukeCodeBridge?style=social)

<img width="1202" height="832" alt="image" src="https://github.com/user-attachments/assets/4ad18972-02a6-4cdf-882e-9aedfba699d0" />


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

## What's New Since v0.12

### v0.15
- **Snippet system** - trigger words with amber highlight, Tab to expand, `$CURSOR$` placeholder
- **Snippet Manager** - personal, shared, and built-in pools with full CRUD
- **Script Info & Comments** - per-script description and team comments, stored in `_meta/` folder
- **Unread comment tracking** - header shows `+N` for unread comments from teammates
- **Smart knobChanged editing** - select node(s) in graph, click Edit knobChanged; falls back to Node Picker if nothing selected
- **Node Picker** - browse/filter all scene nodes, with Pick button (5s countdown, ignores pre-existing selection)
- **Name/Contents search toggle** - filter list by name or search inside all files live
- **Session restore** - untitled tabs with content survive close/reopen
- **Crash recovery autosave** - silent `[!]` tab indicator, right-click to restore or discard
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

## Features (v0.15)

### Network Repository & Sidebar
- **Centralized Storage:** Scripts saved to a shared network path, organized per user.
- **User Sandboxing:** Toggle between your private folder and `all_users` shared repository.
- **Name Search:** Filter scripts live by filename as you type.
- **Contents Search:** Search inside all script files live - opens Find bar on load with your term.
- **scripts/ Subfolder:** New scripts go into `username/scripts/`. Legacy scripts in the root still show up automatically.
- **Right-click menu:** Open folder location or delete any script.

### Multi-Tab Editor
- **Unlimited Workspace:** Open as many scripts as needed in tabs.
- **Dirty State Tracking:** Tabs show `*` when there are unsaved changes.
- **Session Restore:** Untitled tabs with content are saved and restored on reopen.
- **Recently Closed:** Reopen the last closed tab with Ctrl+Shift+T.
- **Duplicate Tab:** Right-click any tab header.

### VS Code-Style Editing
- **Dark+ Professional Theme:** High-contrast syntax highlighting optimized for long sessions.
- **Visual Navigation:** Line numbers, current line highlight, word-occurrence highlight.
- **Indent Guides:** Subtle vertical lines show indentation depth.
- **No Line Wrapping:** Standard IDE behavior to maintain code structure.

### Find & Replace Suite
- **Dual-Row UI:** Dedicated bars for Find and Replace.
- **Bi-Directional Search:** Navigate with Next and Prev controls.
- **Bulk Replacement:** Replace All wrapped in a single undo block.
- **Looping Logic:** Wraps from end back to start automatically.
- **Quick Access:** Ctrl+F to open, Esc to close.

### Snippet System
- Type a **trigger word** and press **Tab** to expand it into a full code block.
- The trigger word gets an **amber highlight** when a snippet match is found (150ms debounce).
- Use `$CURSOR$` in snippet bodies to mark where the cursor lands after expansion.
- **Three pools:** Built-in (read-only), Shared (whole team), Personal (yours only).
- **Snippet Manager** - full CRUD: create, edit, delete, move to shared, insert into editor.

**Built-in triggers:**

| Trigger | Expands to |
|---|---|
| `fornode` | `for node in nuke.selectedNodes():` |
| `ifnuke` | `if nuke:` |
| `tryex` | try/except block |
| `defn` | function definition |
| `blink` | Blink kernel template |
| `blinkp` | Blink param block |

### Script Info & Comments
- Click any script in the sidebar to load its info panel.
- **Description** - document what the script does, saved per script.
- **Comments** - any team member can post a comment; stored in `scripts/_meta/`.
- **Unread tracking** - the collapsed header shows `+N` for comments from teammates you haven't seen yet. Once you open the panel, they're marked as read.
- **Lock file protection** - prevents write conflicts when two people comment at the same time.
- Last 50 comments per script are kept.

### Nuke Integration

**Edit knobChanged**
- Select node(s) in the node graph, click **Edit knobChanged**, and each node opens in its own tab.
- If nothing is selected, the Node Picker expands automatically so you can choose.
- Save writes code back to the node's `knobChanged` knob.
- If the node is deleted, Save As keeps your code as a `.py` file.

**Node Picker**
- Browse and filter all nodes in the current Nuke session.
- **Pick button** - starts a 5-second countdown. Click a node in the graph during the countdown. Pre-existing selections are ignored so you must click something new. Click again to cancel.
- **Refresh** - updates the node list from the scene.

**Run on Selected Nodes** - wraps your script in `for node in nuke.selectedNodes():`. Use `node` in your code.

**Send to Nuke Script Editor** - pushes the current tab's code to Nuke's built-in Script Editor (must be open).

### Save & Backup System
- **Binary Hardened Saving:** Saves in `wb` mode to prevent character mangling.
- **Auto-Backup:** Timestamped `.bak` files in `scripts/_backups/` on every save.
- **Version Control:** Keeps the last 3 versions of every script automatically.
- **Crash Recovery:** Silent `.autosave` every 5 minutes for dirty tabs. Tab shows `[!]` prefix if a newer autosave is found on open - right-click to restore or discard. No popup dialogs.

### Execution Engine
- **Persistent Namespace:** Variables stay in memory between runs.
- **Hardened Execution:** Captures all `stdout`, `stderr`, and full Python tracebacks.
- **Status Light:**
  - Grey: Idle
  - Yellow: Executing
  - Green: Success
  - Red: Error

### Console & Panels
- **Smart Filters:** Toggle between All, Errors Only, and Actions/Info.
- **Console menu:** Soft Refresh, Hard Refresh, Full Reset.
- **Execution History:** Live log of every run. Double-click to restore a snippet.
- **Variable Explorer:** View every variable in the current session namespace.
- **Collapsible panels:** Node Picker, History, Variables, Script Info all collapse to save space.

---

## Configuration

At the top of `nuke_code_bridge.py`:

```python
BASE_SHARED_PATH          = r"\\YOUR_SERVER\YOUR_SHARE\pipeline\NukeScripts"
SHOW_RUN_CONFIRMATION     = True    # ask before running code
USE_SINGLE_SHARED_FOLDER  = False   # True = everyone shares one folder
ENABLE_BACKUPS            = True
MAX_BACKUPS               = 3       # how many .bak versions to keep
MAX_HISTORY_ITEMS         = 25
CONFIRM_OVERWRITE         = False   # True = ask before overwriting on save
AUTOSAVE_INTERVAL_MINUTES = 5       # crash recovery interval (0 = disabled)
```

---

## Installation

### 1. Place the tool file

Copy `nuke_code_bridge.py` into your studio's shared pipeline tools folder:

```
\\YOUR_SERVER\YOUR_SHARE\pipeline\tools\nuke_code_bridge.py
```

### 2. Set up init.py

This tells Nuke where to find `nuke_code_bridge.py` so it can import it.
Set the path via an environment variable (recommended for studios so you don't have to edit this file when paths change) or hardcode it directly:

```python
import os
import nuke

# Option A: set NUKE_CODE_BRIDGE_PATH as a system environment variable on each workstation
# Option B: replace the fallback string below with the actual path on your server
TOOL_PATH = os.environ.get(
    "NUKE_CODE_BRIDGE_PATH",
    r"\\YOUR_SERVER\YOUR_SHARE\pipeline\tools"   # <-- path to the folder containing nuke_code_bridge.py
)

if os.path.exists(TOOL_PATH):
    nuke.pluginAddPath(TOOL_PATH)
else:
    # Using print instead of nuke.message to avoid hanging on render nodes
    print(f"[NukeCodeBridge] Warning: Tool path not found: {TOOL_PATH}")
```

### 3. Set up menu.py

This adds NukeCodeBridge to the Nuke menu.
`importlib.reload` means any updates to `nuke_code_bridge.py` apply the next time
you open the tool - no Nuke restart needed:

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

### 4. Configure BASE_SHARED_PATH inside the tool

Open `nuke_code_bridge.py` and set this at the top:

```python
BASE_SHARED_PATH = r"\\YOUR_SERVER\YOUR_SHARE\pipeline\NukeScripts"
```

> **Two different paths to understand:**
>
> - The **tools folder** set in `init.py` is where `nuke_code_bridge.py` itself lives.
>   Nuke needs this path to be able to import the file.
>
> - `BASE_SHARED_PATH` set inside the tool is the shared network folder where all
>   user script folders, snippets, and comments are stored.
>   Every user on the team needs read/write access to this location.
>
> These can be the same folder, but in most studio setups the tool lives
> in a pipeline tools folder and the data lives in a separate shared folder.

---

## Usage

1. Open Nuke
2. Go to **Scripts > NukeCodeBridge**
3. Select a script from the sidebar or start with a new Untitled tab
4. Edit your Python or Blink code
5. Save with Ctrl+S - first save: enter a filename in the top bar first
6. Run with Ctrl+Enter
7. View output in the console below

---

## Folder Structure

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

## Keyboard Shortcuts

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

## Roadmap

### Completed
- Network repository with per-user sandboxing
- Multi-tab editor with session restore
- VS Code Dark+ theme
- Line numbers, occurrence highlight, indent guides
- Zoom system
- Find & Replace suite
- Go to Line
- Snippet system with personal/shared/built-in pools
- Snippet Manager
- Script Info & Comments with unread tracking
- knobChanged editing with Node Picker
- Pick button with countdown and pre-selection ignore
- Run on Selected Nodes
- Send to Nuke Script Editor
- Crash recovery autosave (silent, right-click to restore)
- Backup system (3 versions)
- Persistent namespace + variable explorer
- Execution history
- Collapsible sidebar panels
- Manual tab built into the tool
- Nuke 15 + 17 compatibility (PySide2 + PySide6)

### Planned
- Git integration
- Per-user settings / preferences
- Script tagging and categories
- Studio read-only protection for shared scripts
- Blink syntax highlighting
- Auto-complete / IntelliSense
- Script templates

---

## Changelog

### v0.15
- Snippet system with Tab expansion and amber highlight
- Snippet Manager (personal / shared / built-in pools)
- Script Info & Comments per script with unread tracking
- Smart knobChanged editing from node graph selection
- Node Picker with Pick countdown (ignores pre-existing selection)
- Name/Contents search toggle
- Session restore for untitled tabs
- Silent crash recovery autosave with tab indicator
- scripts/ subfolder organization with legacy fallback
- Collapsible sidebar panels
- Find & Replace, Go to Line, Reopen Last Closed Tab
- Run on Selected Nodes, Send to Nuke Script Editor
- Full Manual tab built into the tool
- Nuke 15 + 17 compatibility fixes

### v0.12
- Major UI overhaul
- Multi-tab support
- VS Code-style theme
- Word-occurrence + line highlight
- Zoom system
- Improved console
- Backup system rewrite

### v0.11
- Modular refactor
- Basic multi-tab
- Improved repository handling
- Save + backup system
- Console redirection

### v0.9
- Initial public beta
- Single-tab editor
- Basic execution

---

## Requirements

- **Foundry Nuke:** 13.0 or newer (Tested on Nuke 15 and 17)
- **Python:** 3.7+ (Standard with Nuke 13+)
- **Permissions:** Read/Write access to `BASE_SHARED_PATH` for all users

---

## Security & Usage

- **Trust:** Only execute scripts from trusted team members.
- **Caution:** This tool uses Python's `exec()` - just like Nuke's Script Editor.
  Executing unverified code can cause crashes or data loss.
- **Permissions:** Ensure the shared directory has correct read/write access for all users.
- **Beta Software:** Always back up critical scripts before running them.

---

## Contributing

Contributions, discussions, and ideas are welcome!
Submit Pull Requests or open Issues - especially if you are testing on Linux or macOS.

---

## Created by Remco Consten
VFX Artist & Pipeline Enthusiast
<a href="https://www.linkedin.com/in/remcoconsten/" target="_blank">LinkedIn</a>

---
