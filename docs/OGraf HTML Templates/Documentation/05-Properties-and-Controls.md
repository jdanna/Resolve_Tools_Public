# Properties and Fusion Controls

This document explains how OGraf schema properties are mapped to native Fusion UI controls in DaVinci Resolve's Inspector panel.

## Overview

When an OGraf template is loaded, Fusion reads the `schema.properties` from the manifest and creates native Inspector controls for each property. This means your template parameters get the same high-quality controls as built-in Fusion tools - not a generic web form.

**Limits:**
- Maximum **20 dynamic parameters** (schema properties)
- Maximum **10 custom action buttons**

## Property Type Mapping

| JSON Schema Type | GDD Type | Fusion Control | Notes |
|-----------------|----------|---------------|-------|
| `string` | (none) | Text Edit | Standard text input |
| `string` | `single-line` | Text Edit | Same as plain string |
| `string` | `multi-line` | Text Edit | Same control in Fusion |
| `integer` | (none) | Slider | Respects `minimum`, `maximum` |
| `number` | (none) | Slider | Floating-point precision |
| `boolean` | (none) | Checkbox | On/off toggle |
| `string` | `color-rrggbb` | Color Picker (RGB) | Native Fusion COLORCONTROL |
| `string` | `color-rrggbbaa` | Color Picker (RGBA) | With alpha channel |

## Color Properties (Native Integration)

Color properties receive **native Fusion color controls** - the same color picker used throughout Resolve. This provides:

- Visual color wheel/picker
- RGB channel sliders
- Hex value input
- Color management integration (RCM-aware)
- Keyframing support

### Declaring a Color Property

There are several ways Fusion detects a color property. Listed in order of recommendation:

**1. Using gddType (recommended):**

```json
{
  "primaryColor": {
    "type": "string",
    "title": "Primary Color",
    "gddType": "color-rrggbb",
    "pattern": "^#[0-9a-f]{6}$",
    "default": "#cc0000"
  }
}
```

**2. Using gddType with alpha:**

```json
{
  "overlayColor": {
    "type": "string",
    "title": "Overlay Color",
    "gddType": "color-rrggbbaa",
    "pattern": "^#[0-9a-f]{8}$",
    "default": "#cc000080"
  }
}
```

**3. Via pattern field (fallback detection):**

Fusion also detects colors by checking the `pattern` field for hex patterns containing `{6}` (RGB) or `{8}` (RGBA).

**4. Via default value (last resort):**

If the default value looks like a hex color string (`#` followed by 6 or 8 hex characters), Fusion will create a color control.

### How Colors Work Internally

Fusion represents each color as **4 separate channel inputs** (R, G, B, A), each normalized to [0.0, 1.0]:

```
Property "primaryColor" creates:
  - primaryColor_R: 0.0 - 1.0
  - primaryColor_G: 0.0 - 1.0
  - primaryColor_B: 0.0 - 1.0
  - primaryColor_A: 0.0 - 1.0 (hidden if RGB-only)
```

When values are sent back to your graphic, they are converted to hex string format:
- RGB: `"#RRGGBB"` (e.g., `"#cc0000"`)
- RGBA: `"#RRGGBBAA"` (e.g., `"#cc000080"`)

### Using Colors in Your Graphic

The recommended pattern is CSS custom properties:

```javascript
// CSS
:host {
  --primary-color: #cc0000;
}
.headline { background: var(--primary-color); }

// JavaScript (_applyState method)
if (state.primaryColor) {
  this.style.setProperty("--primary-color", state.primaryColor);
}
```

See the Breaking-News example for a template with 7 color properties.

## Numeric Properties

### Integer

```json
{
  "score": {
    "type": "integer",
    "title": "Score",
    "minimum": 0,
    "maximum": 999,
    "default": 0
  }
}
```

Creates a Fusion slider control with integer stepping. The `minimum` and `maximum` values define the slider range.

### Number (Float)

```json
{
  "scale": {
    "type": "number",
    "title": "Global Size",
    "minimum": 0.5,
    "maximum": 2.0,
    "default": 1.0
  }
}
```

Creates a Fusion slider with floating-point precision.

See the Sport-Match-Result example which uses both `integer` (scores) and `number` (scale) properties.

## Boolean Properties

```json
{
  "showCaption": {
    "type": "boolean",
    "title": "Show Caption",
    "default": true
  }
}
```

Creates a Fusion checkbox control.

## String Properties

```json
{
  "headline": {
    "type": "string",
    "title": "Headline",
    "default": "BREAKING NEWS"
  }
}
```

Creates a text edit field in the Inspector.

## Property Ordering

Fusion preserves the order of properties **as they appear in the JSON file**. This is not the default JSON behavior (which sorts alphabetically), so Resolve's parser reads the raw JSON to extract key order.

Design your manifest with properties in the order you want them displayed in the Inspector. Group related properties together:

```json
{
  "properties": {
    "teamAName":  { ... },
    "teamAScore": { ... },
    "teamAColor": { ... },
    "teamBName":  { ... },
    "teamBScore": { ... },
    "teamBColor": { ... }
  }
}
```

## Custom Action Buttons

Custom actions defined in the manifest appear as buttons in the Inspector:

```json
{
  "customActions": [
    {
      "id": "highlight",
      "name": "Highlight",
      "schema": null
    }
  ]
}
```

Each button triggers your `customAction()` method with the corresponding `id`. Maximum 10 action buttons.

## Tips

1. **Stay under 20 properties** - plan your schema carefully
2. **Use colors generously** - native color pickers are a great UX, each color counts as 1 property
3. **Set meaningful defaults** - they appear both in the Inspector and as fallback values
4. **Use descriptive titles** - the `title` field is what users see in the Inspector
5. **Order properties logically** - group related fields (e.g., all Team A properties together)
