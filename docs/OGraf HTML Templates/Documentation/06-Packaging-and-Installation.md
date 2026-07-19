# Packaging and Installation

OGraf graphics can be packaged and distributed in three formats. This document covers each format, how to create them, and where to install them for DaVinci Resolve.

## Packaging Formats

### 1. Raw `.ograf.json` + Assets (Development)

The simplest format - just files in a directory:

```
MyTemplate/
  MyTemplate.ograf.json    # Manifest
  MyTemplate.js            # Web Component
  logo.png                 # Optional assets
```

Place the directory directly in Resolve's template folder for development and testing. No packaging step needed.

**Pros:** Fast iteration during development
**Cons:** Not suitable for distribution

### 2. `.ograf` (dotOgraf - Single Template)

A `.ograf` file is a ZIP archive containing one self-contained template, following the same pattern as dotLottie (`.lottie`).

- **Extension:** `.ograf`
- **MIME type:** `application/zip+ograf`
- **Format:** Standard ZIP archive

```
MyTemplate.ograf (ZIP archive)
  MyTemplate.js
  MyTemplate.ograf.json
```

Resolve discovers manifests inside `.ograf` files using this search order:

1. `<basename>/<basename>.ograf.json` (nested with matching name)
2. `<basename>/manifest.ograf.json` (nested with standard name)
3. `ograf.json` (at root)
4. `<basename>.ograf.json` (at root with basename prefix)
5. `<basename>/ograf.json` (nested without prefix)

Where `<basename>` is the filename without the `.ograf` extension.

**If your template uses shared libraries** (e.g., GSAP), bundle them inside and update import paths:

```
RollingText.ograf
  RollingText/
    manifest.ograf.json
    rolling-text.js        # imports from "./lib/index.js"
    lib/
      index.js
      gsap-core.js
      CSSPlugin.js
```

**Pros:** Self-contained, registered file type, easy to share individual templates
**Cons:** One template per file

### 3. `.drfx` (Distribution Bundle - Recommended)

A `.drfx` file is a ZIP archive with Resolve's template directory structure inside. It can contain multiple templates and is the recommended format for distribution.

**Internal structure:**

```
my-templates.drfx (ZIP archive)
  Edit/
    Titles/
      OGraf/
        Breaking-News.ograf.json
        Breaking-News.js
        Sport-Match-Result.ograf.json
        Sport-Match-Result.js
```

The directory hierarchy maps to Resolve's template browser:
- `Edit/Titles/` - Title templates (shown in Edit page toolbox)
- `Edit/Generators/` - Generator templates
- `Edit/Transitions/` - Transition templates
- `Edit/Effects/` - Effect templates

The subdirectory name under `Titles/` becomes the category name visible to users. For OGraf templates, use `OGraf` as the category.

**Pros:** Multiple templates in one file, installs with double-click, professional distribution
**Cons:** Requires packaging step

### Creating a .drfx File

**Using the provided script:**

```bash
cd "Developer/OGraf HTML Templates/Scripts/"
python3 prepare-drfx.py
```

**Manual creation:**

```bash
# Create staging directory with Resolve structure
mkdir -p staging/Edit/Titles/OGraf
cp MyTemplate.ograf.json staging/Edit/Titles/OGraf/
cp MyTemplate.js staging/Edit/Titles/OGraf/

# Create the .drfx (ZIP archive)
cd staging
zip -r ../my-templates.drfx Edit/
cd ..
rm -rf staging
```

### Creating .ograf (dotOgraf) Files

**Using the provided script:**

```bash
cd "Developer/OGraf HTML Templates/Scripts/"
bash build-dotograf.sh
```

**Manual creation:**

```bash
# For a simple template (no shared libs)
zip MyTemplate.ograf MyTemplate.ograf.json MyTemplate.js

# For a template with shared libs
zip -r MyTemplate.ograf MyTemplate/ -x '*.DS_Store'
```

## Installation Directories

### Per-User Templates (recommended for development)

Place templates in the user template directory. No administrator privileges required.

**macOS:**
```
~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Templates/Edit/Titles/<YourCategory>/
```

**Windows** (`%APPDATA%` = `C:\Users\<username>\AppData\Roaming`):
```
%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Templates\Edit\Titles\<YourCategory>\
```

### Global Templates (system-wide, all users)

Templates available to all users on the system. No administrator privileges required for either platform.

**macOS:**
```
/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Templates/Edit/Titles/<YourCategory>/
```

**Windows:**
```
C:\ProgramData\Blackmagic Design\DaVinci Resolve\Fusion\Templates\Edit\Titles\<YourCategory>\
```

### DRFX Installation

Double-clicking a `.drfx` file in Finder/Explorer will install it into Resolve's template directory automatically. The internal directory structure of the DRFX determines where templates appear.

### Template Discovery

Resolve scans template directories for these file types:
- `.ograf.json` - Raw manifest files
- `.ograf` - dotOgraf packages (ZIP archives, `application/zip+ograf`)
- `.drfx` - Template bundles (ZIP archives with directory structure)

Scanning happens at startup and when templates change. After adding files manually, restart Resolve or refresh the template browser.

## Packaging Best Practices

1. **Use `.drfx` for distribution** - it's the cleanest format for end users
2. **Use raw files for development** - fastest iteration cycle
3. **Keep templates self-contained** - no external CDN dependencies, no fetch calls
4. **Include all assets** - fonts, images, any shared libraries
5. **Test after packaging** - verify the ZIP/DRFX loads correctly in a fresh Resolve session
6. **Use descriptive category names** - the subdirectory name appears in the template browser
7. **Set `accessToPublicInternet: false`** in renderRequirements - templates should not require internet access

## Example: Full Packaging Workflow

```bash
# 1. Develop your template
mkdir -p ~/ograf-dev/MyLowerThird/
# ... create MyLowerThird.ograf.json and MyLowerThird.js

# 2. Test in Resolve (raw files)
TEMPLATES=~/Library/Application\ Support/Blackmagic\ Design/DaVinci\ Resolve/Fusion/Templates
mkdir -p "$TEMPLATES/Edit/Titles/OGraf"
cp ~/ograf-dev/MyLowerThird/* "$TEMPLATES/Edit/Titles/OGraf/"
# Restart Resolve, test the template

# 3. Package as .ograf (dotOgraf single template)
cd ~/ograf-dev/MyLowerThird
zip MyLowerThird.ograf MyLowerThird.ograf.json MyLowerThird.js

# 4. Package as .drfx (distribution bundle)
mkdir -p staging/Edit/Titles/OGraf
cp ~/ograf-dev/MyLowerThird/*.ograf.json staging/Edit/Titles/OGraf/
cp ~/ograf-dev/MyLowerThird/*.js staging/Edit/Titles/OGraf/
cd staging && zip -r ../ograf-templates.drfx Edit/ && cd .. && rm -rf staging
```
