# Resolve Tools

A collection of custom-built tools for **DaVinci Resolve** — Python automation scripts, CLI utilities, DCTL color effects, and Fusion compositing macros.

---

## Python Scripts (`Python/`)

### Timeline Management

#### `DUPLICATE.py`
Duplicates the current timeline once and auto-increments the name (e.g. `Cut 3` → `Cut 4`). Sets the new duplicate as the active timeline.

#### `DUPLICATE NUM.py`
Same as above but prompts for how many copies to make, creating each with an incremented name.

#### `CREATE TIMELINES.py`
Takes every clip in the current media pool folder and creates a separate timeline for each one, named after the clip (without extension). Useful for organizing individual clips into their own sequences.

---

### Timecode & Segment Tools

#### `BATCH SET TC.py`
Prompts for a timecode value and applies it as the start timecode to every clip in the current media pool folder.

#### `BATCH SET SEQUENCE TC.py`
Prompts for a timecode value and applies it as the start timecode to every **sequence (timeline)** in the current media pool folder. Ignores source clips.

#### `SEGTIMES.py`
Reads the current timeline's In/Out points and outputs the segment duration in the format:
```
HH:MM:SS:FF - HH:MM:SS:FF  TRT HH:MM:SS:FF
```

---

## CLI Tools (`Python/CLI/`)

Scripts for navigating and managing the **DaVinci Resolve Project Manager** from the command line. All list commands output JSON.

| Script | Usage | Description |
|---|---|---|
| `open.py` | `python3 open.py <project_name>` | Open a project by name |
| `import.py` | `python3 import.py <project_name>` | Create and import a project from a template (`.drp`) |
| `mkdir.py` | `python3 mkdir.py <folder_name>` | Create a folder in the current project manager location |
| `cd.py` | `python3 cd.py <folder_name>` | Navigate into a folder |
| `parent.py` | `python3 parent.py` | Navigate to the parent folder |
| `root.py` | `python3 root.py` | Navigate to the root folder |
| `listproj.py` | `python3 listproj.py` | List projects in the current folder (JSON array) |
| `listfolders.py` | `python3 listfolders.py` | List folders in the current location (JSON array) |
| `listsubfolders.py` | `python3 listsubfolders.py` | List subfolders line by line |
| `jsonlist.py` | `python3 jsonlist.py` | Recursively dump the full project tree as JSON |

---

## DCTLs (`DCTL/`)

### `LETTERBOX.dctl`
Fills the top and bottom of frame with a solid color to achieve a target aspect ratio.

| Parameter | Range | Default | Description |
|---|---|---|---|
| Ratio | 1.0 – 5.0 | 2.35 | Target aspect ratio |
| Red / Green / Blue | 0.0 – 1.0 | 1 / 0 / 0 | Bar color |

### `PILLARBOX.dctl`
Fills the left and right sides of frame with a solid color.

| Parameter | Range | Default | Description |
|---|---|---|---|
| Percent | 1.0 – 100.0 | 2.35 | Width percentage for each bar |
| Red / Green / Blue | 0.0 – 1.0 | 1 / 0 / 0 | Bar color |

### `JOESAT V3.dctl`
Saturation and subtractive saturation tool with multi-format color space support. Decodes log to linear, converts to AP1 (ACES), applies HSV-based saturation adjustments, then re-encodes back to log.

| Parameter | Range | Default | Description |
|---|---|---|---|
| Color Space | — | ACEScct | Input/output color space: ACEScct, ARRI LogC3, Cineon Log, DaVinci Intermediate |
| Subsat | 0 – 0.2 | 0 | Subtractive saturation — reduces saturation and luminance in proportion to existing color |
| Color Boost | 0 – 2 | 1 | Overall saturation multiplier |

### `TITLESAFE.dctl`
Displays configurable safe area guides (action safe, title safe, center crosshair).

| Parameter | Description |
|---|---|
| Enable Outer / Inner / Center | Toggle each guide independently |
| Outer Box | Outer safe area size as percentage of frame diagonal (default 90%) |
| Inter Box | Inner safe area size as percentage of frame diagonal (default 80%) |
| Thickness | Line width for each box guide |
| Aspect | Guide aspect ratio (default 1.77 for 16:9) |
| Center Size | Size of the center crosshair |
| Red / Green / Blue | Guide color |

### `BLANKING.dctl`
Edge blanking detector — highlights areas in the border region that fall below a brightness threshold, useful for catching dirty edges or mattes.

| Parameter | Range | Default | Description |
|---|---|---|---|
| Threshold | 0.0 – 1.0 | 0.02 | Brightness level below which blanking is flagged |
| Border | 0 – 100 | 100 | Border area percentage to inspect |
| Red / Green / Blue | 0.0 – 1.0 | 1 / 0 / 0 | Highlight color for flagged pixels |

---

## Fusion Macros (`Fusion/`)

### `SUBTITLE.setting`
A text overlay macro with a background box. Controls:
- Text content (StyledText), font, style, size, color, tracking, and line spacing
- Background box color, transparency, and padding (width/height)
- Position and movement controls

### `UNBAKE INTERLACE.setting`
Vertically resamples baked-in interlacing to clean up visible lines. Controls:
- **RESAMPLE** (70–99): Resampling quality
- **BLANKING RECOVER** (0–25): Artifact recovery for blanking edges
- Sharpen and punch-in/zoom controls

### `TEST PATTERN GENERATOR.setting`
Generates video test patterns for QA and display calibration.

**Pattern types** (via `GENERATE`): White, Grey, Red, Green, Blue, Grayscale gradient

**Color spaces** (via `COLORSPACE`): Rec.709, ST2084 1000 nit HDR, ST2084 3000 nit HDR

**PATCH SIZE** (0–100%): Scale the pattern within the frame
