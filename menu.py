# ==============================================================================
# NukeCodeBridge - menu.py
# ==============================================================================
#
# PURPOSE:
#   Adds NukeCodeBridge to the Nuke menu so artists can launch it.
#
# HOW IT WORKS:
#   importlib.reload() is used so that any changes made to nuke_code_bridge.py
#   are applied the next time you launch it — without restarting Nuke.
#   Useful during development or when the studio pushes updates.
#
# ICON (optional):
#   Place a .png file in the same folder as this menu.py and set the
#   icon parameter below to its filename, e.g. icon='NukeCodeBridge.png'
# ==============================================================================

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
    icon='',      # Optional: 'NukeCodeBridge.png'
    tooltip='Network-based Python script manager for studio teams.'
)
