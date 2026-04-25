## 🗺️ Roadmap

The development of **NukeCodeBridge** follows a "Stability, then Scalability" approach.

### 🔴 Phase 1: High Priority (Stability & Safety)
- ✅ **Safety Net:** Automatic backup creation (.bak) before overwriting any existing script.
- ✅ **Namespace Isolation:** Execution engine runs code in a protected namespace to prevent global variable pollution.
- ☑️ **Expanded File Support:** Basic support for any file type via Save As. Dedicated syntax handling for `.nk`, `.gizmo`, and `.json` planned.
- ✅ **Improved UX:** Unsaved changes indicator (`*` on tabs), status bar warnings, confirmation dialogs.

### 🟡 Phase 2: Medium Priority (Organization & Scaling)
- ⬜ **Update Notifier:** GitHub API check to notify users if a newer version is available.
- ⬜ **Studio Protection:** Read-Only attribute for official repositories to prevent accidental edits.
- ⬜ **Tagging System:** Category-based filtering (e.g., Color, Transform, Admin).
- ⬜ **Discovery UI:** Clickable tag pills above the script list for rapid browsing.
- ⬜ **Recent Files:** Quick-access menu for the last 10 scripts opened.

### 🟢 Phase 3: Nice-to-Have (Optimization & Polish)
- ✅ **Integrated Console:** Output window for `print()` results and full Python tracebacks.
- ✅ **Deep Search:** Search inside the content of all scripts live.
- ✅ **Auto-Save:** Background crash recovery autosave with configurable interval.
- ✅ **Sidecar Metadata:** Hidden `.json` files for per-script descriptions and team comments.

### 🔵 Phase 4: Long-Term (Advanced Workflow)
- ⬜ **Auto-Updater:** Automatic sync allowing the tool to update itself while preserving user settings via a separate `config.json`.
- ⬜ **Drag & Drop:** Drag scripts directly into the editor from the OS file browser.
- ⬜ **Approval Pipeline:** Visual flag system (e.g., "Draft" vs. "Production Ready") for studio-wide tool vetting.
