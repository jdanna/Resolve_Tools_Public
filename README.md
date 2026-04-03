# Resolve Tools

A collection of custom-built tools for **DaVinci Resolve** — Python automation scripts, CLI utilities, DCTL color effects, and Fusion compositing macros.

---

## Python Scripts (`Python/`)

### Timeline Management

#### `DUPLICATE.py`
Duplicates the current timeline once and auto-increments the name (e.g. `Cut 3` → `Cut 4`). Sets the new duplicate as the active timeline.

<img width="169" height="88" alt="Screenshot 2026-04-02 at 10 20 55 PM" src="https://github.com/user-attachments/assets/fb6814d1-aa81-492a-bc02-0af5f58ab7f3" />

#### `DUPLICATE NUM.py`
Same as above but prompts for how many copies to make, creating each with an incremented name.

<img width="264" height="125" alt="Screenshot 2026-04-02 at 10 21 07 PM" src="https://github.com/user-attachments/assets/45e2240f-1a4f-4424-a7d5-c63028a3117e" />

#### `CREATE TIMELINES.py`
Takes every clip in the current media pool folder and creates a separate timeline for each one, named after the clip (without extension). Useful for organizing individual clips into their own sequences, with matching start timecode.

<img width="378" height="349" alt="Screenshot 2026-04-02 at 10 34 55 PM" src="https://github.com/user-attachments/assets/34c23f63-55ac-4a12-bb34-08aff9b9bcb0" />

---

### Timecode & Segment Tools

#### `BATCH SET TC.py`
Prompts for a timecode value and applies it as the start timecode to every clip in the current media pool folder.

<img width="304" height="125" alt="Screenshot 2026-04-02 at 10 21 47 PM" src="https://github.com/user-attachments/assets/b34d4299-0170-4621-8aa6-22727a49a8af" />

#### `BATCH SET SEQUENCE TC.py`
Prompts for a timecode value and applies it as the start timecode to every **sequence (timeline)** in the current media pool folder. Ignores source clips.

<img width="325" height="131" alt="Screenshot 2026-04-02 at 10 22 36 PM" src="https://github.com/user-attachments/assets/9d5d00ef-3339-4489-9b54-a3f7b2b0f574" />

#### `SEGTIMES.py`
Reads the current timeline's In/Out points and outputs the segment duration in the format:
```
HH:MM:SS:FF - HH:MM:SS:FF  TRT HH:MM:SS:FF
```
Outputs to clipboard and to console.

<img width="454" height="141" alt="Screenshot 2026-04-02 at 10 23 29 PM" src="https://github.com/user-attachments/assets/eb2cccc7-5a9d-4850-a9cd-d1143cfd7f8b" />

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

<img width="1178" height="440" alt="Screenshot 2026-04-02 at 10 31 36 PM" src="https://github.com/user-attachments/assets/c8b0a6a9-5522-408e-84fb-987090b96bbf" />

| Parameter | Range | Default | Description |
|---|---|---|---|
| Ratio | 1.0 – 5.0 | 2.35 | Target aspect ratio |
| Red / Green / Blue | 0.0 – 1.0 | 1 / 0 / 0 | Bar color |

### `PILLARBOX.dctl`
Fills the left and right sides of frame with a solid color.

<img width="1172" height="439" alt="Screenshot 2026-04-02 at 10 31 53 PM" src="https://github.com/user-attachments/assets/840f87f4-2c1c-4f58-b2f3-c483b1db0d6b" />

| Parameter | Range | Default | Description |
|---|---|---|---|
| Percent | 1.0 – 100.0 | 2.35 | Width percentage for each bar |
| Red / Green / Blue | 0.0 – 1.0 | 1 / 0 / 0 | Bar color |

### `JOESAT V3.dctl`
Saturation and subtractive saturation tool with multi-format color space support. Decodes log to linear, converts to AP1 (ACES), applies HSV-based saturation adjustments, then re-encodes back to log.

<img width="415" height="175" alt="Screenshot 2026-04-02 at 10 27 19 PM" src="https://github.com/user-attachments/assets/4e996330-89ac-42d0-9067-fe3dfe6da194" />

| Parameter | Range | Default | Description |
|---|---|---|---|
| Color Space | — | ACEScct | Input/output color space: ACEScct, ARRI LogC3, Cineon Log, DaVinci Intermediate |
| Subsat | 0 – 0.2 | 0 | Subtractive saturation — reduces saturation and luminance in proportion to existing color |
| Color Boost | 0 – 2 | 1 | Overall saturation multiplier |

### `TITLESAFE.dctl`
Displays configurable safe area guides (action safe, title safe, center crosshair).

<img width="1174" height="435" alt="Screenshot 2026-04-02 at 10 32 30 PM" src="https://github.com/user-attachments/assets/fa72e246-6b5e-41d0-88ca-42e7ca14a728" />

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

<img width="1183" height="455" alt="Screenshot 2026-04-02 at 10 29 56 PM" src="https://github.com/user-attachments/assets/69709119-a816-4b84-b0b9-e1666c0609e0" />

| Parameter | Range | Default | Description |
|---|---|---|---|
| Threshold | 0.0 – 1.0 | 0.02 | Brightness level below which blanking is flagged |
| Border | 0 – 100 | 100 | Border area percentage to inspect |
| Red / Green / Blue | 0.0 – 1.0 | 1 / 0 / 0 | Highlight color for flagged pixels |

---

## Fusion Macros (`Fusion/`)

### `UNBAKE INTERLACE.setting`
Vertically resamples baked-in interlacing to clean up visible lines. Controls:
- **RESAMPLE** (70–99): Resampling quality
- **BLANKING RECOVER** (0–25): Artifact recovery for blanking edges
- Sharpen and punch-in/zoom controls

<img width="416" height="185" alt="Screenshot 2026-04-02 at 10 39 00 PM" src="https://github.com/user-attachments/assets/b935fa9e-51c6-4e2d-be9b-2d89051f0618" />

### `TEST PATTERN GENERATOR.setting`
Generates video test patterns for QA and display calibration.

<img width="939" height="431" alt="Screenshot 2026-04-02 at 10 39 40 PM" src="https://github.com/user-attachments/assets/79073aaa-28e3-4042-979c-07ba97c71ecc" />

**Pattern types** (via `GENERATE`): White, Grey, Red, Green, Blue, Grayscale gradient

**Color spaces** (via `COLORSPACE`): Rec.709, ST2084 1000 nit HDR, ST2084 3000 nit HDR

**PATCH SIZE** (0–100%): Scale the pattern within the frame
