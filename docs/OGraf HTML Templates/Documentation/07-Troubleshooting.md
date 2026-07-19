# Troubleshooting

## Common Issues

### Template not appearing in Resolve

**Symptoms:** Template doesn't show up in the Edit page toolbox after installation.

**Checks:**
1. Verify the manifest filename ends with `.ograf.json`
2. Check the file is in the correct directory: `Fusion/Templates/Edit/Titles/<Category>/`
3. Ensure the manifest has all required fields (`$schema`, `id`, `name`, `main`, `supportsRealTime`, `supportsNonRealTime`)
4. Restart Resolve after adding new template files
5. If using `.drfx`, verify the internal ZIP structure starts with `Edit/Titles/...`
6. OGraf is not supported on Linux or iOS

### Blank/black output

**Symptoms:** Template appears in toolbox but renders as blank or black when added to timeline.

**Checks:**
1. Verify `supportsNonRealTime` is `true` in the manifest
2. Ensure `goToTime()` is implemented and calls `_setFrame()`
3. Check that `_setFrame()` sets `scene.style.opacity = "1"` for valid timestamps
4. Verify the `main` field points to the correct JS file
5. Confirm the JS file has `export default ClassName;`
6. Make sure you're NOT calling `customElements.define()` in your JS

### Animation not playing / stuck on first frame

**Symptoms:** The graphic appears but doesn't animate during playback.

**Checks:**
1. `goToTime()` must convert milliseconds to seconds: `timestamp / 1000`
2. Ensure `_setFrame()` calculates element positions based on the `seconds` parameter
3. Do NOT use `setTimeout`, `setInterval`, or `requestAnimationFrame` for animation
4. Do NOT call `.play()` on CSS animations or GSAP timelines
5. Verify `v_bmd.duration` in manifest matches your animation length

### Colors not showing as color pickers

**Symptoms:** Color properties appear as text inputs instead of native color pickers.

**Checks:**
1. Add `"gddType": "color-rrggbb"` (or `"color-rrggbbaa"`)
2. Add `"pattern": "^#[0-9a-f]{6}$"` (or `{8}` for RGBA, lowercase only)
3. Set a valid hex default: `"default": "#cc0000"`
4. Ensure the property `type` is `"string"`

### Properties not appearing in Inspector

**Symptoms:** Some or all properties don't show in Resolve's Inspector panel.

**Checks:**
1. Maximum 20 properties - check you're under the limit
2. Ensure `schema.type` is `"object"` and properties are under `schema.properties`
3. Each property must have a `type` field (`"string"`, `"number"`, `"integer"`, `"boolean"`)

### Inconsistent rendering on scrub/export

**Symptoms:** Different visual results when scrubbing vs. playing, or export looks different from preview.

**Checks:**
1. `goToTime()` with the same timestamp MUST produce identical output
2. No `Math.random()` without seeding
3. No async operations that might not complete before frame capture
4. No dependency on call order or previous frames
5. No CSS transitions or animations (use manual property calculation instead)

### updateAction not reflecting changes

**Symptoms:** Changing a property in the Inspector doesn't update the graphic.

**Checks:**
1. `updateAction()` must merge new data: `this._state = { ...this._state, ...(params.data || {}) }`
2. Call `_applyState()` after merging to update DOM
3. For colors: update CSS custom properties via `this.style.setProperty()`

## Debugging Tips

### Check manifest validity

Validate your `.ograf.json` against the schema:
```
https://ograf.ebu.io/v1/specification/json-schemas/graphics/schema.json
```

### Test in a browser

You can test your Web Component in a standalone HTML page before loading in Resolve:

```html
<!DOCTYPE html>
<html>
<body style="width:1920px;height:1080px;background:#333;position:relative;">
<script type="module">
  import MyGraphic from './MyGraphic.js';
  customElements.define('my-graphic', MyGraphic);
  const el = document.createElement('my-graphic');
  el.style.cssText = 'position:absolute;inset:0;';
  document.body.appendChild(el);

  await el.load({ data: {}, renderType: 'non-realtime',
    renderCharacteristics: { resolution: { width: 1920, height: 1080 }, frameRate: 30 }
  });
  await el.playAction({ delta: 1 });

  // Test seeking
  for (let ms = 0; ms <= 5000; ms += 100) {
    await el.goToTime({ timestamp: ms });
    await new Promise(r => setTimeout(r, 33));
  }
</script>
</body>
</html>
```

### Verify determinism

Call `goToTime()` with the same timestamp twice and compare the visual output:

```javascript
await el.goToTime({ timestamp: 1500 });
// capture frame 1
await el.goToTime({ timestamp: 3000 });
await el.goToTime({ timestamp: 1500 });
// capture frame 2 - must be identical to frame 1
```

## Performance

### Keep DOM simple
- Minimize the number of DOM elements
- Use CSS transforms (`translate`, `scale`, `rotate`) instead of `top`/`left`/`width`/`height` for animation
- Avoid `backdrop-filter` and complex box-shadows during animation

### Minimize layout thrashing
- Batch DOM reads before DOM writes
- Use `will-change` on animated elements (sparingly)
- Avoid triggering layout recalculation in `_setFrame()`

### Efficient `_setFrame()`
- This method is called for every frame - keep it fast
- Pre-calculate values that don't change (e.g., element references, ticker width)
- Use `.toFixed()` to avoid unnecessary decimal precision in CSS values
- Cache `scrollWidth`/`offsetWidth` measurements
