## 🚀 Future Features & Roadmap
The development of **NukeCodeBridge** follows a "Stability, then Scalability" approach.
### 🔴 Phase 1: High Priority (Stability & Safety)
 * **Safety Net:** Implement automatic backup creation (.bak) before overwriting any existing script.
 * **Namespace Isolation:** Update the execution engine to run code in a protected namespace to prevent global variable "pollution" between different scripts.
 * **Expanded File Support:** Integration of .nk (scene files), .gizmo, and .json support for broader pipeline utility.
 * **Improved UX:** Clearer confirmation dialogs and "Status Bar" warnings for unsaved changes.
### 🟡 Phase 2: Medium Priority (Organization & Scaling)
 * **Studio Protection:** Add a **Read-Only** attribute for "Official" or "Studio" repositories to prevent accidental edits to core tools.
 * **Tagging System:** Implement a category-based filtering system (e.g., Color, Transform, Admin) using metadata headers.
 * **Discovery UI:** Add clickable "Tag Pills" above the script list for rapid browsing.
 * **Recent Files:** A quick-access menu for the last 10 scripts opened by the current user.
### 🟢 Phase 3: Nice-to-Have (Optimization & Polish)
 * **Integrated Console:** A mini output window within the UI to view print() results and Python tracebacks without opening the Nuke terminal.
 * **Deep Search:** Functionality to search **inside** the content of scripts rather than just the filenames.
 * **Auto-Save:** Optional background saving (with a toggle) to preserve work-in-progress code.
 * **Sidecar Metadata:** Implementation of hidden .json files to support user **comments** and threaded feedback per script.
### 🔵 Phase 4: Long-Term (Advanced Workflow)
 * **Drag & Drop:** Allow artists to drag scripts directly into the editor from their OS file browser.
 * **Archive Tools:** One-click export of a user repository into a .zip for easy migration or backup.
 * **Approval Pipeline:** A visual flag system (e.g., "Draft" vs. "Production Ready") for studio-wide tool vetting.
