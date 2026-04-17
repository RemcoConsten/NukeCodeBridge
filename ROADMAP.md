## 🚀 Future Features & Roadmap
The development of **NukeCodeBridge** follows a "Stability, then Scalability" approach.
### 🔴 Phase 1: High Priority (Stability & Safety)
 * **Safety Net:** Implement automatic backup creation (.bak) before overwriting any existing script.
 * **Namespace Isolation:** Update the execution engine to run code in a protected namespace to prevent global variable "pollution."
 * **Expanded File Support:** Integration of .nk (scene files), .gizmo, and .json support.
 * **Improved UX:** Clearer confirmation dialogs and "Status Bar" warnings for unsaved changes.
### 🟡 Phase 2: Medium Priority (Organization & Scaling)
 * **Update Notifier:** Implement a GitHub API check to notify users if a newer version of NukeCodeBridge is available.
 * **Studio Protection:** Add a **Read-Only** attribute for "Official" repositories to prevent accidental edits.
 * **Tagging System:** Implement a category-based filtering system (e.g., Color, Transform, Admin).
 * **Discovery UI:** Add clickable "Tag Pills" above the script list for rapid browsing.
 * **Recent Files:** A quick-access menu for the last 10 scripts opened.
### 🟢 Phase 3: Nice-to-Have (Optimization & Polish)
 * **Integrated Console:** A mini output window within the UI to view print() results and Python tracebacks.
 * **Deep Search:** Functionality to search **inside** the content of scripts.
 * **Auto-Save:** Optional background saving (with a toggle) to preserve work-in-progress code.
 * **Sidecar Metadata:** Implementation of hidden .json files to support user **comments** per script.
### 🔵 Phase 4: Long-Term (Advanced Workflow)
 * **Auto-Updater:** Transition from "Notification" to "Automatic Sync," allowing the tool to update itself while preserving user settings via a separate config.json.
 * **Drag & Drop:** Allow artists to drag scripts directly into the editor from their OS file browser.
 * **Approval Pipeline:** A visual flag system (e.g., "Draft" vs. "Production Ready") for studio-wide tool vetting.
