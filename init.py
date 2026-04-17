import os
import nuke

# ==============================================================================
# NukeCodeBridge - Init
# ==============================================================================

# You can set an environment variable 'NUKE_CODE_BRIDGE_PATH' on the system
# or simply replace the string below with your studio's tool path.
REPO_PATH = os.environ.get("NUKE_CODE_BRIDGE_PATH", r"\\YOUR_SERVER\YOUR_SHARE\pipeline\tools")

if os.path.exists(REPO_PATH):
    nuke.pluginAddPath(REPO_PATH)
else:
    # We use print instead of nuke.message to prevent render-node hanging
    print(f"[NukeCodeBridge] Warning: Path not found: {REPO_PATH}")
