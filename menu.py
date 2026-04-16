import nuke

# ========================
# NukeCodeBridge Menu Entry
# ========================

def launch_nuke_code_bridge():
    """Launch NukeCodeBridge v0.5 beta"""
    try:
        import NukeCodeBridge
        NukeCodeBridge.start_nuke_code_bridge()
    except Exception as e:
        nuke.message(f"Failed to load NukeCodeBridge:\n{str(e)}")

# Add tool to the Nuke menu
nuke.menu('Nuke').addCommand(
    'Scripts/NukeCodeBridge', 
    launch_nuke_code_bridge,
    shortcut=None,                    # Change to 'Shift+C' or similar if you want a hotkey
    tooltip='NukeCodeBridge v0.5 beta - Network Script Manager'
)
