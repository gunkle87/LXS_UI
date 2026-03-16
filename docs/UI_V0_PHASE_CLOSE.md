# UI v0 Phase Close

## What v0 Supports

- PySide6 workbench with bounded board viewport, drag placement, and orthogonal autorouted traces
- Single-selection editing for components, traces, and nodes
- Copy, paste, duplicate, delete, undo, redo, and project save/load through the menu path
- DLL-backed engine bridge using the admitted public `lxs_api.dll` boundary
- Simple simulation stepping with component/pad state coloring
- Lightweight inspector and status readout for selected objects, engine tick state, and probe values

## What Is Deferred

- waveform or timeline tooling
- richer simulation controls beyond simple step/toggle
- broader primitive export support beyond the current v0 engine-bridge set
- deeper runtime inspection panels and polish work
- post-v0 architecture cleanup that is not required for the current workbench

## How To Run It

1. Open a terminal in `C:\DEV\LXS_UI`.
2. Activate the virtual environment:
   ```cmd
   .venv\Scripts\activate
   ```
3. Launch the workbench:
   ```cmd
   scripts\launch.bat
   ```

## Practical v0 Flow

1. Place or load a small board using `input`, `and`, `output`, and `probe`.
2. Use `Toggle Selected Input` on the selected input components.
3. Click `Step`.
4. Check:
   - component/pad state accents on the board
   - inspector labels for selected objects
   - status bar tick and probe summary text

## Validation Baseline

- full UI test suite passing
- menu and tool wiring verified
- save/load round-trip verified
- engine step path verified through the admitted DLL bridge
- `C:\DEV\LXS` unchanged during UI work
