# Web Component API Reference

An OGraf graphic is an HTML Custom Element (Web Component) that extends `HTMLElement`. The class must be the **default export** of the JavaScript file referenced by the manifest's `main` field.

## Requirements

1. **Extend `HTMLElement`**
2. **Use Shadow DOM** - attach via `this.attachShadow({ mode: "open" })`
3. **Export as default** - `export default MyGraphic;`
4. **Do NOT call `customElements.define()`** - the host registers the element
5. **Implement all 8 methods** listed below

## Minimal Skeleton

```javascript
const DEFAULT_STATE = {
  headline: "HELLO WORLD",
};

class MyGraphic extends HTMLElement {
  constructor() {
    super();
    this._state = { ...DEFAULT_STATE };
    this._initialData = {};
    this._currentStep = 0;
    this._schedule = [];

    const root = this.attachShadow({ mode: "open" });
    const style = document.createElement("style");
    style.textContent = `
      :host { position: absolute; inset: 0; display: block; }
      .scene { position: absolute; inset: 0; opacity: 0; }
    `;

    const scene = document.createElement("div");
    scene.className = "scene";

    root.append(style, scene);
    this._scene = scene;
  }

  async load(params) {
    this._initialData = params.data || {};
    this._state = { ...DEFAULT_STATE, ...this._initialData };
    this._schedule = [];
    this._applyState();
    this._setFrame(0);
    return { statusCode: 200 };
  }

  async dispose() {
    this._scene.remove();
    return { statusCode: 200 };
  }

  async playAction(params) {
    this._currentStep = 1;
    this._setFrame(0.5);
    return { statusCode: 200, currentStep: this._currentStep };
  }

  async stopAction(params) {
    this._currentStep = 0;
    this._setFrame(-1);
    return { statusCode: 200 };
  }

  async updateAction(params) {
    this._state = { ...this._state, ...(params.data || {}) };
    this._applyState();

    // Keep _initialData in sync so goToTime state resets preserve edits.
    // Only skip if the schedule contains its own updateAction events
    // that would replay the data during goToTime.
    const hasUpdateInSchedule = this._schedule.some(e => e.action?.type === "updateAction");
    if (!hasUpdateInSchedule) {
      this._initialData = { ...this._initialData, ...(params.data || {}) };
    }

    return { statusCode: 200 };
  }

  async customAction(params) {
    return { statusCode: 200 };
  }

  async goToTime(payload) {
    const timestamp = payload?.timestamp ?? 0;

    // Reset to initial state and replay schedule events up to timestamp.
    // This ensures deterministic output for any given timestamp.
    this._state = { ...DEFAULT_STATE, ...this._initialData };
    this._applyState();

    let lastPlayTimestamp = null;
    let lastStopTimestamp = null;

    for (const event of this._schedule) {
      if (event.timestamp > timestamp) break;
      const { type, params } = event.action;
      if (type === "updateAction") {
        this._state = { ...this._state, ...(params?.data || {}) };
        this._applyState();
      } else if (type === "playAction") {
        lastPlayTimestamp = event.timestamp;
        lastStopTimestamp = null;
        this._currentStep = 1;
      } else if (type === "stopAction") {
        lastStopTimestamp = event.timestamp;
        lastPlayTimestamp = null;
        this._currentStep = 0;
      }
    }

    if (lastStopTimestamp !== null) {
      const elapsed = (timestamp - lastStopTimestamp) / 1000;
      this._setFrame(-1 + elapsed);
    } else if (lastPlayTimestamp !== null) {
      const elapsed = (timestamp - lastPlayTimestamp) / 1000;
      this._setFrame(elapsed);
    } else {
      this._setFrame(timestamp / 1000);
    }

    return { statusCode: 200 };
  }

  async setActionsSchedule(payload) {
    this._schedule = payload.schedule || [];
    return { statusCode: 200 };
  }

  _applyState() {
    // Update DOM from this._state
  }

  _setFrame(seconds) {
    // Position all elements for the given timestamp
    if (this._currentStep === 0) {
      this._scene.style.opacity = "0";
      return;
    }
    const duration = 5;
    if (seconds < 0 || seconds > duration) {
      this._scene.style.opacity = "0";
      return;
    }
    this._scene.style.opacity = "1";
    // ... animate elements based on seconds
  }
}

export default MyGraphic;
```

## Method Reference

### load(params)

Called when the graphic is loaded into the DOM.

**Parameters:**
```javascript
{
  data: { ... },                    // Initial state (matches manifest schema)
  renderType: "non-realtime",       // Always "non-realtime" in Resolve
  renderCharacteristics: {
    resolution: { width: 1920, height: 1080 },
    frameRate: 30
  }
}
```

**Return:** `{ statusCode: 200 }`

**Implementation:**
- Merge `params.data` with default state
- Build DOM elements
- Call `_setFrame(0)` to set initial hidden state

### dispose()

Called when the graphic is removed. Clean up all resources.

**Return:** `{ statusCode: 200 }`

**Implementation:**
- Remove DOM elements
- Kill any GSAP timelines: `tl.kill()`
- Clear references

### playAction(params)

Makes the graphic visible and starts/advances animation.

**Parameters:**
```javascript
{
  delta: 1,              // Relative step movement (default: 1)
  goto: undefined,       // Absolute step number (optional)
  skipAnimation: false   // Skip intro animation
}
```

**Return:** `{ statusCode: 200, currentStep: 1 }`

**Implementation:**
- Set `_currentStep` based on delta/goto
- Call `_setFrame()` at a visible position (e.g., 0.5 seconds in)

### stopAction(params)

Hides the graphic (animate out).

**Parameters:**
```javascript
{
  skipAnimation: false   // Skip outro animation
}
```

**Return:** `{ statusCode: 200 }`

**Implementation:**
- Set `_currentStep = 0`
- Call `_setFrame(-1)` to move to hidden state

### updateAction(params)

Updates data while the graphic is playing. Called when the operator changes a property value in Resolve's Inspector.

**Parameters:**
```javascript
{
  data: { ... },         // Partial or full state update
  skipAnimation: false
}
```

**Return:** `{ statusCode: 200 }`

**Implementation:**
- Merge new data into existing state
- Re-apply state (colors, text, etc.)
- **Critical for non-real-time**: also update `_initialData` so that `goToTime()` state resets preserve the user's edits. Only skip this if the schedule contains its own `updateAction` events that replay the data during seeks:

```javascript
const hasUpdateInSchedule = this._schedule.some(e => e.action?.type === "updateAction");
if (!hasUpdateInSchedule) {
  this._initialData = { ...this._initialData, ...(params.data || {}) };
}
```

### customAction(params)

Executes a custom action defined in the manifest's `customActions` array.

**Parameters:**
```javascript
{
  id: "highlight",       // Action ID from manifest
  payload: { ... },      // Action-specific data
  skipAnimation: false
}
```

**Return:** `{ statusCode: 200 }`

### goToTime(time) - Critical for Resolve

Seeks to a specific timestamp for frame-by-frame rendering. **This is the most important method for Resolve.**

**Parameters:**
```javascript
{
  timestamp: 1500        // Time in milliseconds
}
```

**Return:** `{ statusCode: 200 }`

**Requirements:**
- Same timestamp MUST always produce identical visual output
- Must handle any timestamp value (forward, backward, random access)
- Must be synchronous in its visual effect (no async rendering)
- Timestamps outside `[0, duration*1000]` should show hidden state

**Implementation:**
The recommended implementation resets to initial state, replays the schedule up to the requested timestamp, then positions elements:

```javascript
async goToTime(payload) {
  const timestamp = payload?.timestamp ?? 0;

  // Reset to initial state so each seek is deterministic
  this._state = { ...DEFAULT_STATE, ...this._initialData };
  this._applyState();

  let lastPlayTimestamp = null;
  let lastStopTimestamp = null;

  for (const event of this._schedule) {
    if (event.timestamp > timestamp) break;
    const { type, params } = event.action;
    if (type === "updateAction") {
      this._state = { ...this._state, ...(params?.data || {}) };
      this._applyState();
    } else if (type === "playAction") {
      lastPlayTimestamp = event.timestamp;
      lastStopTimestamp = null;
      this._currentStep = 1;
    } else if (type === "stopAction") {
      lastStopTimestamp = event.timestamp;
      lastPlayTimestamp = null;
      this._currentStep = 0;
    }
  }

  if (lastStopTimestamp !== null) {
    const elapsed = (timestamp - lastStopTimestamp) / 1000;
    this._setFrame(-1 + elapsed);
  } else if (lastPlayTimestamp !== null) {
    const elapsed = (timestamp - lastPlayTimestamp) / 1000;
    this._setFrame(elapsed);
  } else {
    this._setFrame(timestamp / 1000);
  }

  return { statusCode: 200 };
}
```

**Important**: The state reset at the top (`{ ...DEFAULT_STATE, ...this._initialData }`) means `updateAction` must keep `_initialData` in sync with user edits. Otherwise the reset will revert typed text or other property changes.

### setActionsSchedule(schedule)

Pre-schedules actions at specific timestamps. The host calls this before `goToTime()` to provide a timeline of actions that the graphic must replay during seeks.

**Parameters:**
```javascript
{
  schedule: [
    { timestamp: 0,    action: { type: "playAction", params: {} } },
    { timestamp: 5000, action: { type: "stopAction",  params: {} } }
  ]
}
```

**Return:** `{ statusCode: 200 }`

**Implementation:**
Store the schedule for use during `goToTime()` replays:
```javascript
async setActionsSchedule(payload) {
  this._schedule = payload.schedule || [];
  return { statusCode: 200 };
}
```

The OGraf runtime injects a default schedule (`playAction` at timestamp 0) when no external schedule is provided, so the graphic always has at least one event to replay.

## Return Format

All methods return a Promise resolving to:

```javascript
{
  statusCode: 200,           // HTTP-style status code
  statusMessage: "OK",       // Optional human-readable message
  result: undefined,         // Optional graphics-specific data
  currentStep: 1             // Only for playAction()
}
```

If a method returns `undefined`, it is treated as `{ statusCode: 200 }`.

## Step Model

The `stepCount` in the manifest controls playAction behavior:

| stepCount | Model | Behavior |
|-----------|-------|----------|
| `0` | Fire & Forget | Auto-animates in and out, no manual stop |
| `1` (default) | Single Step | play shows, stop hides |
| `>1` | Multi-Step | Multiple playAction calls advance through steps |
| `-1` | Dynamic | Variable number of steps |

For most Resolve title templates, `stepCount: 1` is appropriate.

## Common Helper Functions

### Easing

```javascript
function clamp(v, min, max) {
  return Math.max(min, Math.min(v, max));
}

function easeOutCubic(t) {
  return 1 - Math.pow(1 - t, 3);
}

function easeOutBack(t) {
  const c1 = 1.70158;
  const c3 = c1 + 1;
  return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
}
```

### Phased Animation Pattern

Structure your `_setFrame()` with sequential phases:

```javascript
_setFrame(seconds) {
  // Phase 1: Title fade in (0 - 0.3s)
  const titleProgress = easeOutCubic(clamp(seconds / 0.3, 0, 1));
  title.style.opacity = String(titleProgress);

  // Phase 2: Content slide in (0.1 - 0.5s)
  const contentProgress = easeOutBack(clamp((seconds - 0.1) / 0.4, 0, 1));
  content.style.transform = `translateX(${(-60 + 60 * contentProgress).toFixed(1)}px)`;

  // Phase 3: Details appear (0.5 - 1.0s)
  const detailProgress = easeOutCubic(clamp((seconds - 0.5) / 0.5, 0, 1));
  details.style.opacity = String(detailProgress);
}
```

## CSS Variables for Colors

Use CSS custom properties to pass color values from state to styles:

```javascript
// In CSS
:host {
  --primary-color: #cc0000;
}
.headline { background: var(--primary-color); }

// In _applyState()
if (s.primaryColor) this.style.setProperty("--primary-color", s.primaryColor);
```

This pattern integrates cleanly with Fusion's native color picker controls.
