# ==============================================================================
# NukeCodeBridge - init.py
# ==============================================================================
#
# PURPOSE:
#   Registers the folder where nuke_code_bridge.py lives with Nuke's plugin
#   system, so Nuke can find and import it when menu.py calls it.
#
# HOW TO SET THE PATH:
#   Option A — Environment variable (recommended for studios):
#     Set NUKE_CODE_BRIDGE_PATH on each workstation to point to the folder
#     containing nuke_code_bridge.py. This way you don't need to edit this
#     file when the path changes.
#
#   Option B — Hardcode it:
#     Replace the fallback string below with the actual path on your server.
#
# NOTE:
#   This path is where the TOOL FILE lives, not where scripts are stored.
#   The shared script/data folder is configured separately inside
#   nuke_code_bridge.py using BASE_SHARED_PATH.
# ==============================================================================

import os
import nuke

TOOL_PATH = os.environ.get(
    "NUKE_CODE_BRIDGE_PATH",
    r"\\YOUR_SERVER\YOUR_SHARE\pipeline\tools"   # <-- change this to your path
)

if os.path.exists(TOOL_PATH):
    nuke.pluginAddPath(TOOL_PATH)
else:
    # Using print instead of nuke.message to avoid hanging on render nodes
    print(f"[NukeCodeBridge] Warning: Tool path not found: {TOOL_PATH}")
