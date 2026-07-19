# Resolve Integration Guide

This is the most important document for OGraf template developers targeting DaVinci Resolve. It covers Resolve-specific requirements that differ from general OGraf/live broadcast usage.

## NonRealTime is Mandatory

Resolve's OGraf renderer advertises itself as:

```
supportsRealTime:    false
supportsNonRealTime: true
```

**Your manifest MUST set:**

```json
{
  "supportsRealTime": false,
  "supportsNonRealTime": true
}
```

This means your graphic MUST implement `goToTime()` and `setActionsSchedule()`.

### Why NonRealTime?

Resolve is a post-production NLE (non-linear editor), not a live broadcast playout system. When a user scrubs the timeline, plays back, or exports, Resolve calls `goToTime(timestamp)` for each frame. The graphic must render the correct visual for that exact timestamp, whether playing forward, backward, or jumping randomly.

Real-time-only graphics (those with only `supportsRealTime: true`) receive a polyfill fallback, but this is suboptimal and may produce incorrect frames during scrubbing or export.

## Deterministic Rendering

**The #1 rule**: calling `goToTime()` with the same timestamp must ALWAYS produce identical visual output.

This means:

- **No `Math.random()`** without seeding - use a deterministic PRNG if you need randomness
- **No async operations** in `goToTime()` - all state must be computed synchronously
- **No timers** (`setTimeout`, `setInterval`, `requestAnimationFrame`) for animation
- **No `.play()` calls** on CSS animations or GSAP timelines - use seeking only
- **All animation state** must be calculable from the timestamp alone

### Recommended Pattern: `_setFrame(seconds)`

Implement a pure function that positions all elements based on the current time:

```javascript
async goToTime(time) {
  const timestamp = time?.timestamp ?? 0;
  this._setFrame(timestamp / 1000);  // Convert ms to seconds
  return { statusCode: 200 };
}

_setFrame(seconds) {
  const duration = 5; // your animation duration

  // Hidden state - outside animation range
  if (seconds < 0 || seconds > duration) {
    this._elements.scene.style.opacity = "0";
    return;
  }

  this._elements.scene.style.opacity = "1";

  // Calculate animation progress for each element
  const progress = easeOutCubic(clamp(seconds / 0.3, 0, 1));
  this._elements.title.style.opacity = String(progress);
  this._elements.title.style.transform =
    `translateY(${(20 - 20 * progress).toFixed(1)}px)`;
}
```

### Seeded Randomness (if needed)

```javascript
function createRNG(seed) {
  let s = seed | 0;
  return function () {
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
```

## Duration and Timeline Integration

The `v_bmd.duration` field in the manifest controls the **clip length** in Resolve's timeline:

```json
{
  "v_bmd": {
    "duration": 5
  }
}
```

- Duration is in **seconds**
- Resolve converts this to frames based on the timeline frame rate
- Users can trim the clip shorter but cannot extend it beyond the declared duration
- Set duration to match your total animation length (intro + hold + outro)

## Frame Rate

The `renderRequirements.frameRate` field hints at the intended animation frame rate:

```json
{
  "renderRequirements": [{
    "frameRate": { "ideal": 30 }
  }]
}
```

Resolve uses this alongside the timeline frame rate to determine seek granularity. In practice, `goToTime()` is called at the timeline's frame rate.

## Property Limits

Fusion's OGrafLoader has fixed limits:

- **Maximum 20 dynamic parameters** (schema properties)
- **Maximum 10 custom action buttons**
- Colors count as a single parameter (even though they use 4 internal channels)

Plan your schema accordingly. If you need more than 20 properties, consider grouping related values or using string fields with structured formats.

## Color Properties (Native Support)

Properties declared as colors get **native Fusion color picker controls** with full color management integration:

```json
{
  "primaryColor": {
    "title": "Primary Color",
    "type": "string",
    "gddType": "color-rrggbb",
    "pattern": "^#[0-9a-f]{6}$",
    "default": "#cc0000"
  }
}
```

See [05-Properties-and-Controls.md](05-Properties-and-Controls.md) for full details on color support.

## Color Space Handling

When Resolve Color Management (RCM) is enabled, OGraf output undergoes sRGB-to-linear gamma conversion automatically. When RCM is off, sRGB gamma is preserved. You do not need to handle this in your graphic - the OGrafLoader manages the conversion.

## Platform Availability

| Platform | OGraf Support |
|----------|--------------|
| macOS    | Full support (Metal GPU acceleration on Apple Silicon) |
| Windows  | Full support (CPU rendering) |
| Linux    | Not supported |
| iOS      | Not supported |

## GPU Acceleration

Frame capture from CEF is GPU-accelerated on macOS:

- **macOS**: Metal compute shader (IOSurface -> image, with sRGB/linear conversion and vertical flip)
- **Windows / Fallback**: CPU readback

This is transparent to graphic developers - no action needed.

## Lifecycle in Resolve

When a user adds an OGraf title to the timeline:

1. `load({ data, renderType: "non-realtime", renderCharacteristics })` is called
2. `playAction()` is called (for initial visibility)
3. For each rendered frame: `goToTime({ timestamp })` is called
4. When properties change in the Inspector: `updateAction({ data })` is called
5. When the clip is removed: `dispose()` is called

**Important**: `goToTime()` may be called with ANY timestamp in ANY order - forward, backward, or random access. Your graphic must handle this correctly.
