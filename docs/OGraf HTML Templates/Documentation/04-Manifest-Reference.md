# Manifest Reference (.ograf.json)

The manifest file is the entry point for an OGraf graphic. It must have a filename ending in `.ograf.json`.

## Complete Example

```json
{
  "$schema": "https://ograf.ebu.io/v1/specification/json-schemas/graphics/schema.json",
  "id": "my-company-lower-third",
  "version": "1.0.0",
  "name": "Lower Third",
  "description": "Professional lower-third graphic with name and title.",
  "author": {
    "name": "My Company",
    "email": "dev@example.com",
    "url": "https://example.com"
  },
  "main": "lower-third.js",
  "v_bmd": {
    "duration": 5
  },
  "stepCount": 1,
  "supportsRealTime": false,
  "supportsNonRealTime": true,
  "schema": {
    "type": "object",
    "properties": {
      "name": {
        "type": "string",
        "title": "Name",
        "default": "John Doe"
      },
      "title": {
        "type": "string",
        "title": "Title",
        "default": "Reporter"
      },
      "accentColor": {
        "type": "string",
        "title": "Accent Color",
        "gddType": "color-rrggbb",
        "pattern": "^#[0-9a-f]{6}$",
        "default": "#2563eb"
      }
    }
  },
  "renderRequirements": [
    {
      "resolution": {
        "width": { "ideal": 1920 },
        "height": { "ideal": 1080 }
      },
      "frameRate": { "ideal": 30 }
    }
  ]
}
```

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `$schema` | string | Must be `"https://ograf.ebu.io/v1/specification/json-schemas/graphics/schema.json"` |
| `id` | string | Unique identifier. No forward slashes. Recommended: reverse domain notation or simple kebab-case |
| `name` | string | Display name shown to users in Resolve |
| `main` | string | Path to JavaScript file (relative to manifest) |
| `supportsRealTime` | boolean | Set `false` for Resolve |
| `supportsNonRealTime` | boolean | Set `true` for Resolve |

## Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `version` | string | - | Semantic version (e.g., `"1.0.0"`) |
| `description` | string | - | Longer description (1-2 sentences) |
| `author` | object | - | `{ name, email?, url? }` - at least `name` required |
| `v_bmd` | object | - | Vendor-specific BMD extensions object (see below) |
| `stepCount` | integer | 1 | Number of interaction steps (see below) |
| `schema` | object | - | JSON Schema defining operator-editable parameters |
| `customActions` | array | - | Custom action definitions |
| `renderRequirements` | array | - | Resolution, frame rate requirements |

### The `v_bmd` Object

The `v_bmd` object contains Blackmagic Design vendor-specific fields:

```json
{
  "v_bmd": {
    "duration": 5
  }
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `duration` | number | `10` | Animation duration in seconds. Controls clip length in Resolve timeline |

### Vendor-Specific Fields

Any field prefixed with `v_` is allowed for vendor-specific extensions:

```json
{
  "v_myCustomField": "any value"
}
```

## Schema (Properties)

The `schema` field defines parameters that become editable controls in Resolve's Inspector.

### Property Types

#### String

```json
{
  "headline": {
    "type": "string",
    "title": "Headline",
    "default": "BREAKING NEWS"
  }
}
```

#### Number (floating-point)

```json
{
  "scale": {
    "type": "number",
    "title": "Scale",
    "minimum": 0.5,
    "maximum": 2.0,
    "default": 1.0
  }
}
```

#### Integer

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

#### Boolean

```json
{
  "showBadge": {
    "type": "boolean",
    "title": "Show Badge",
    "default": true
  }
}
```

#### Color (RGB)

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

#### Color (RGBA with alpha)

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

#### Select (dropdown)

```json
{
  "position": {
    "type": "string",
    "title": "Position",
    "enum": ["top", "center", "bottom"],
    "gddType": "select",
    "gddOptions": {
      "labels": {
        "top": "Top",
        "center": "Center",
        "bottom": "Bottom"
      }
    },
    "default": "bottom"
  }
}
```

### GDD Type Reference

GDD (Graphics Data Definition) types provide GUI hints that gracefully degrade to their base JSON Schema type:

| gddType | Base Type | Resolve UI Control | Notes |
|---------|-----------|-------------------|-------|
| `single-line` | string | Text edit | |
| `multi-line` | string | Text area | |
| `color-rrggbb` | string | Fusion color picker (RGB) | Requires `pattern`: `^#[0-9a-f]{6}$` (lowercase only) |
| `color-rrggbbaa` | string | Fusion color picker (RGBA) | Requires `pattern`: `^#[0-9a-f]{8}$` (lowercase only) |
| `select` | string/number/integer | Dropdown | Requires `enum` and `gddOptions` with `labels` |
| `percentage` | number | Percentage slider (0-1) | |
| `duration-ms` | integer | Duration in milliseconds | |
| `file-path` | string | File picker | Optional `gddOptions.extensions` (e.g. `[".json", ".xml"]`) |
| `file-path/image-path` | string | Image file picker | Optional `gddOptions.extensions` (e.g. `[".png", ".jpg"]`) |

## Step Count

| Value | Model | Description |
|-------|-------|-------------|
| `0` | Fire & Forget | Graphic auto-animates in and out |
| `1` (default) | Single Step | `playAction()` shows, `stopAction()` hides |
| `>1` | Multi-Step | Multiple `playAction()` calls advance through steps |
| `-1` | Dynamic | Variable number of steps, negotiated at runtime |

For most Resolve title templates, use `stepCount: 1`.

## Custom Actions

Define custom action buttons that appear in the Resolve Inspector:

```json
{
  "customActions": [
    {
      "id": "highlight",
      "name": "Highlight",
      "description": "Flash a highlight effect",
      "schema": null
    },
    {
      "id": "setTheme",
      "name": "Set Theme",
      "schema": {
        "type": "object",
        "properties": {
          "theme": { "type": "string", "enum": ["light", "dark"] }
        }
      }
    }
  ]
}
```

**Resolve limit**: Maximum 10 custom actions.

## Render Requirements

Specify resolution and frame rate expectations:

```json
{
  "renderRequirements": [
    {
      "resolution": {
        "width": { "ideal": 1920 },
        "height": { "ideal": 1080 }
      },
      "frameRate": { "ideal": 30 },
      "accessToPublicInternet": { "ideal": false }
    }
  ]
}
```

### Constraint Types

**NumberConstraint** (for resolution width/height, frameRate):
- `min` - Minimum acceptable value
- `max` - Maximum acceptable value
- `exact` - Must be this exact value
- `ideal` - Preferred value

**BooleanConstraint** (for accessToPublicInternet):
- `exact` - Must be this value
- `ideal` - Preferred value

## Manifest for Resolve Checklist

- [ ] `$schema` set to the official EBU schema URL
- [ ] `id` is unique (no forward slashes)
- [ ] `name` is descriptive
- [ ] `main` points to your .js file
- [ ] `supportsRealTime` is `false`
- [ ] `supportsNonRealTime` is `true`
- [ ] `v_bmd.duration` matches your animation length in seconds
- [ ] `schema.properties` has at most 20 properties
- [ ] `customActions` has at most 10 actions
- [ ] Color properties use `gddType: "color-rrggbb"` or `"color-rrggbbaa"`
