# OGraf Overview

## What is OGraf?

OGraf is an open standard developed by the [EBU (European Broadcasting Union)](https://www.ebu.ch/) for **web-based broadcast graphics**. It enables interoperability between graphics developers, controllers, and renderers by standardizing how graphics are packaged, described, and controlled.

- **Official specification**: https://github.com/ebu/ograf/tree/main/v1
- **JSON Schema**: https://ograf.ebu.io/v1/specification/json-schemas/graphics/schema.json

## Core Concepts

### Graphic

An OGraf graphic is a self-contained package consisting of:

1. **Manifest** (`.ograf.json`) - Metadata describing the graphic: name, parameters, duration, capabilities
2. **Web Component** (`.js`) - An HTML Custom Element that renders the graphic
3. **Assets** (optional) - Images, fonts, or other resources

### Manifest

The manifest file (ending in `.ograf.json`) is the entry point. It declares:

- **Identity**: `id`, `name`, `version`, `author`
- **Entry point**: `main` - path to the JavaScript file
- **Capabilities**: `supportsRealTime`, `supportsNonRealTime`
- **Parameters**: `schema` - JSON Schema defining operator-editable properties
- **Timing**: `v_bmd.duration`, `stepCount`
- **Requirements**: `renderRequirements` - resolution, frame rate

### Web Component

The JavaScript file exports a class extending `HTMLElement` with 8 required methods:

| Method | Purpose |
|--------|---------|
| `load()` | Initialize graphic with data |
| `dispose()` | Clean up resources |
| `playAction()` | Start or advance animation |
| `stopAction()` | Hide/animate out |
| `updateAction()` | Update data while playing |
| `customAction()` | Execute custom actions |
| `goToTime()` | Seek to timestamp (non-real-time) |
| `setActionsSchedule()` | Pre-schedule actions (non-real-time) |

### Actions

Graphics respond to **actions** from the host:

- **play** - Makes the graphic visible, starts intro animation
- **stop** - Animates out and hides
- **update** - Changes data (e.g., operator edits a text field)
- **custom** - Graphics-specific actions defined in the manifest

### Data Schema (GDD)

Parameters are defined using **GDD (Graphics Data Definition)** - a JSON Schema extension with GUI-friendly type hints. Properties in the schema become editable controls in the host application.

## How Resolve Uses OGraf

DaVinci Resolve renders OGraf graphics through Fusion's **OGrafLoader** tool:

1. **Discovery** - Resolve scans template directories for `.ograf.json`, `.ograf` (dotOgraf), and `.drfx` files
2. **Loading** - When a user adds an OGraf title, the manifest is parsed and the Web Component is loaded into a CEF (Chromium) browser instance
3. **UI Generation** - Schema properties are mapped to native Fusion controls (sliders, text fields, color pickers, checkboxes)
4. **Rendering** - Resolve calls `goToTime()` for each frame during playback/export, capturing the CEF output as image data
5. **Compositing** - The rendered frame is composited over the timeline video

**Key architectural point**: Resolve operates in **non-real-time** mode. It does not play animations in real-time - instead, it seeks to exact timestamps frame-by-frame. This is fundamentally different from live broadcast playout.

See [02-Resolve-Integration.md](02-Resolve-Integration.md) for detailed Resolve-specific requirements.
