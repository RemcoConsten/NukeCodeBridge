import nuke
import importlib

# ==============================================================================
# NukeCodeBridge - Menu Entry
# ==============================================================================

def launch_nuke_code_bridge():
    """
    Imports and launches the NukeCodeBridge UI.
    Using importlib.reload ensures code changes are applied without restarting Nuke.
    """
    try:
        import nuke_code_bridge
        importlib.reload(nuke_code_bridge)
        nuke_code_bridge.start_nuke_code_bridge()
    except Exception as e:
        nuke.message(f"Failed to load NukeCodeBridge:\n{str(e)}")

# Add to the Nuke 'Nodes' menu or the top 'Nuke' menu bar
toolbar = nuke.menu('Nuke')
toolbar.addCommand(
    'Scripts/NukeCodeBridge', 
    launch_nuke_code_bridge, 
    icon='', # Optional: add a .png icon name here
    tooltip='Network-based Python script manager for studio teams.'
)
