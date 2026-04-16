# NukeCodeBridge
NukeCodeBridge is a lightweight mini IDE for Nuke that centralizes Python script management. It features a network-synced file system, Python syntax highlighting, and cross-version support (PySide2/6). It eliminates the need to manually copy-paste scripts between artists by providing a shared, searchable repository accessible from the Nuke menu.


Here is a complete, ready-to-paste README.md file formatted perfectly for GitHub. You can copy everything below and paste it directly into your GitHub repository.
# Nuke Network Script Manager
A lightweight, network-ready mini-IDE for Foundry's Nuke. This tool allows pipeline developers and compositors to write, save, run, and share Python scripts across a shared studio network directly from inside Nuke.
## ✨ Features
 * **Network-Ready:** Saves scripts to user-specific folders on a shared network drive.
 * **Smart Code Editor:** Includes Python syntax highlighting, line numbers, tab-to-spaces conversion, and smart auto-indentation.
 * **Unsaved Changes Tracking:** Warns you before accidentally closing or switching scripts if you have unsaved work.
 * **Code Execution:** Run the entire script, or highlight specific lines to execute only the selection.
 * **Quick Search:** Live-filtering search bar to easily find scripts in large directories.
 * **Context Menu:** Right-click scripts to Rename, Delete, Run, or Copy their exact network path to share with colleagues.
 * **Cross-Version Compatible:** Automatically handles PySide2 (Nuke 13 and below) and PySide6 (Nuke 14+).
## 🚀 Installation Guide
Installing this tool requires configuring a central server location for the tool itself, and then updating each user's local Nuke configuration files to load it.
### Step 1: Server Setup (Do this once)
 1. Create a directory on your shared server to store Nuke plugins. For example: Z:\Pipeline\NukePlugins
 2. Create a secondary directory on your server where the actual user scripts will be saved. For example: Z:\Pipeline\SharedNukeScripts
 3. Download network_script_manager.py and place it in your plugins folder.
 4. Open the file and update the SHARED_SERVER_PATH variable at the top of the script to match your scripts folder:
```python
# network_script_manager.py
SHARED_SERVER_PATH = r"Z:\Pipeline\SharedNukeScripts" 

```
### Step 2: Client Setup (Do this for each user)
To load the tool into Nuke, you need to modify the user's init.py and menu.py files. These are located in the user's .nuke directory:
 * **Windows:** C:\Users\<Username>\.nuke
 * **Mac:** /Users/<Username>/.nuke
 * **Linux:** /home/<Username>/.nuke
#### 1. Update init.py
Open init.py (create it if it doesn't exist) and add the following code to tell Nuke where to find the plugin on the server:
```python
import nuke

# Add the server directory to Nuke's plugin path
nuke.pluginAddPath(r"Z:\Pipeline\NukePlugins")

```
#### 2. Update menu.py
Open menu.py (create it if it doesn't exist) and add the following code to create a custom top-menu button and keyboard shortcut (Ctrl+Shift+M):
```python
import nuke

# Create a new top-level menu dropdown
custom_menu = nuke.menu('Nuke').addMenu('Studio Tools')

# Add the command to launch the UI
custom_menu.addCommand('Network Script Manager', 'import network_script_manager; network_script_manager.start_network_manager()', 'ctrl+shift+m')

```
## 📖 How to Use
 1. Launch Nuke and click **Studio Tools > Network Script Manager** in the top menu bar.
 2. **Writing Code:** Type or paste your Python code into the text editor. Hold Ctrl and scroll your mouse wheel to zoom the font in or out.
 3. **Saving:** Enter a name in the top text field and click **Save to Current User**. It will automatically be saved as a .py file under your username on the network.
 4. **Running Code:** Click **Run Code** to execute the script in Nuke. If you highlight a specific block of text, only that highlighted portion will run.
 5. **Viewing Others:** Use the dropdown menu on the left to select a colleague's name. You can view, load, and run their saved scripts.
 6. **File Management:** Right-click any script in the list to trigger the context menu, allowing you to easily rename, delete, or copy the file path.
## 🛠️ Requirements
 * Foundry Nuke 11.0 or higher.
 * Compatible with both PySide2 and PySide6.
 * Network read/write permissions for the target deployment directory.
