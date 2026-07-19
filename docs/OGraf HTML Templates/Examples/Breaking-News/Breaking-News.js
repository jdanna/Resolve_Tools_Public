
const DEFAULT_STATE = {
  liveBadgeText: "LIVE",
  subtitle: "LOREM IPSUM DOLOR SIT AMET",
  breakingText: "BREAKING",
  newsText: "NEWS",
  categoryLabel: "LOREM IPSUM",
  headline: "HEADLINE HERE",
  tickerText:
    "LOREM IPSUM DOLOR SIT AMET, CONSECTETUER ADIPISCING ELIT, SED DIAM NONUMMY NIBH EUISMOD TINCIDUNT",
  liveBadgeColor: "#c0392b",
  subtitleBarColor: "#1a1a1a",
  breakingBgColor: "#1a2744",
  newsBgColor: "#f0c030",
  categoryColor: "#2563eb",
  headlineColor: "#c0392b",
  tickerBgColor: "#f5f3ee",
};

function clamp(v, min, max) {
  return Math.max(min, Math.min(v, max));
}

function easeOutCubic(t) {
  return 1 - Math.pow(1 - t, 3);
}

const STYLE_TEXT = `
:host {
  position: absolute;
  inset: 0;
  display: block;
  pointer-events: none;
  font-family: "Arial", "Helvetica Neue", sans-serif;
  --live-badge-color: #c0392b;
  --subtitle-bar-color: #1a1a1a;
  --breaking-bg-color: #1a2744;
  --news-bg-color: #f0c030;
  --category-color: #2563eb;
  --headline-color: #c0392b;
  --ticker-bg-color: #f5f3ee;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

.scene {
  position: absolute;
  inset: 0;
  opacity: 0;
  will-change: opacity;
}

/* ── Top-Left Logo Bug ── */
.logo-bug {
  position: absolute;
  top: 50px;
  left: 60px;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.logo-top-row {
  display: flex;
  align-items: stretch;
  height: 30px;
}

.live-badge {
  background: var(--live-badge-color);
  color: #fff;
  font-weight: 800;
  font-style: italic;
  font-size: 18px;
  padding: 0 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  letter-spacing: 0.05em;
  flex-shrink: 0;
}

.subtitle-bar {
  background: var(--subtitle-bar-color);
  color: #fff;
  font-weight: 600;
  font-size: 14px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.logo-bottom-row {
  display: flex;
  align-items: stretch;
  height: 52px;
}

.breaking-text {
  background: var(--breaking-bg-color);
  color: #fff;
  font-weight: 900;
  font-size: 38px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  letter-spacing: 0.02em;
  line-height: 1;
}

.news-text {
  background: var(--news-bg-color);
  color: #1a1a1a;
  font-weight: 900;
  font-size: 38px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  letter-spacing: 0.02em;
  line-height: 1;
  border: 2px solid #333;
  border-left: none;
}

/* ── Bottom Lower Third ── */
.lower-third {
  position: absolute;
  bottom: 80px;
  left: 0;
  right: 60px;
  will-change: transform, opacity;
}

.side-panel {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 55px;
  background: #000;
  will-change: transform;
}

.lower-content {
  margin-left: 55px;
  display: flex;
  flex-direction: column;
}

.category-row {
  display: flex;
  align-items: stretch;
  will-change: opacity, transform;
}

.category-label {
  background: var(--category-color);
  color: #fff;
  font-weight: 800;
  font-size: 18px;
  padding: 6px 24px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  display: flex;
  align-items: center;
  white-space: nowrap;
}

.headline-row {
  display: flex;
  align-items: stretch;
  will-change: transform;
}

.headline-bar {
  background: var(--headline-color);
  color: #fff;
  font-weight: 800;
  font-style: italic;
  font-size: 52px;
  padding: 10px 30px;
  display: flex;
  align-items: center;
  white-space: nowrap;
  letter-spacing: 0.01em;
  line-height: 1.1;
}

.ticker-row {
  position: relative;
  height: 40px;
  background: var(--ticker-bg-color);
  overflow: hidden;
  will-change: transform;
  transform-origin: left center;
  border-bottom: 2px solid rgba(0,0,0,0.08);
}

.ticker-text {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  display: flex;
  align-items: center;
  white-space: nowrap;
  font-weight: 700;
  font-style: italic;
  font-size: 20px;
  color: #1a1a1a;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  will-change: transform;
  padding-right: 100px;
}
`;

class BreakingNewsV2Graphic extends HTMLElement {
  constructor() {
    super();
    this._state = { ...DEFAULT_STATE };
    this._isVisible = false;
    this._currentStep = 1;
    this._animations = [];
    this._tickerWidth = 0;

    const root = this.attachShadow({ mode: "open" });
    const style = document.createElement("style");
    style.textContent = STYLE_TEXT;

    // Scene
    const scene = document.createElement("div");
    scene.className = "scene";

    // ── Logo Bug ──
    const logoBug = document.createElement("div");
    logoBug.className = "logo-bug";

    const logoTopRow = document.createElement("div");
    logoTopRow.className = "logo-top-row";

    const liveBadge = document.createElement("div");
    liveBadge.className = "live-badge";

    const subtitleBar = document.createElement("div");
    subtitleBar.className = "subtitle-bar";

    logoTopRow.append(liveBadge, subtitleBar);

    const logoBottomRow = document.createElement("div");
    logoBottomRow.className = "logo-bottom-row";

    const breakingTextEl = document.createElement("div");
    breakingTextEl.className = "breaking-text";

    const newsTextEl = document.createElement("div");
    newsTextEl.className = "news-text";

    logoBottomRow.append(breakingTextEl, newsTextEl);
    logoBug.append(logoTopRow, logoBottomRow);

    // ── Lower Third ──
    const lowerThird = document.createElement("div");
    lowerThird.className = "lower-third";

    const sidePanel = document.createElement("div");
    sidePanel.className = "side-panel";

    const lowerContent = document.createElement("div");
    lowerContent.className = "lower-content";

    const categoryRow = document.createElement("div");
    categoryRow.className = "category-row";

    const categoryLabel = document.createElement("div");
    categoryLabel.className = "category-label";

    categoryRow.append(categoryLabel);

    const headlineRow = document.createElement("div");
    headlineRow.className = "headline-row";

    const headlineBar = document.createElement("div");
    headlineBar.className = "headline-bar";

    headlineRow.append(headlineBar);

    const tickerRow = document.createElement("div");
    tickerRow.className = "ticker-row";

    const tickerText = document.createElement("div");
    tickerText.className = "ticker-text";

    tickerRow.append(tickerText);

    lowerContent.append(categoryRow, headlineRow, tickerRow);
    lowerThird.append(sidePanel, lowerContent);

    scene.append(logoBug, lowerThird);
    root.append(style, scene);

    this._elements = {
      scene,
      logoBug,
      liveBadge,
      subtitleBar,
      breakingTextEl,
      newsTextEl,
      sidePanel,
      lowerThird,
      categoryRow,
      categoryLabel,
      headlineRow,
      headlineBar,
      tickerRow,
      tickerText,
    };
  }

  connectedCallback() {}

  async load(params) {
    this._initialData = params.data || {};
    this._state = { ...DEFAULT_STATE, ...this._initialData };
    this._schedule = [];
    this._applyState();
    this._setFrame(0);
    return { statusCode: 200 };
  }

  async dispose() {
    this._cancelAnimations();
    this._elements.scene.remove();
    return { statusCode: 200 };
  }

  async playAction(params) {
    const targetStep = this._resolveTargetStep(params);
    this._currentStep = targetStep;

    if (targetStep > 0) {
      this._setFrame(0.5);
    }

    return { statusCode: 200, currentStep: this._currentStep };
  }

  async stopAction(params) {
    this._currentStep = 0;
    this._setFrame(-1);
    return { statusCode: 200 };
  }

  async updateAction(params) {
    this._state = { ...this._state, ...(params.data || {}) };
    this._initialData = { ...this._initialData, ...(params.data || {}) };
    this._applyState();
    return { statusCode: 200 };
  }

  async customAction() {
    return { statusCode: 200 };
  }

  async setActionsSchedule(payload) {
    this._schedule = (payload.schedule || []).slice().sort((a, b) => a.timestamp - b.timestamp);
    return { statusCode: 200 };
  }

  async goToTime(payload) {
    const timestamp = payload?.timestamp ?? 0;

    this._state = { ...DEFAULT_STATE, ...this._initialData };
    this._currentStep = 1;
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
        this._currentStep = this._resolveTargetStep(params);
      } else if (type === "stopAction") {
        lastStopTimestamp = event.timestamp;
        lastPlayTimestamp = null;
        this._currentStep = 0;
      }
    }

    if (lastStopTimestamp !== null) {
      this._setFrame(-1);
    } else if (lastPlayTimestamp !== null) {
      const elapsed = (timestamp - lastPlayTimestamp) / 1000;
      this._setFrame(elapsed);
    } else {
      this._setFrame(timestamp / 1000);
    }

    return { statusCode: 200 };
  }

  _applyState() {
    const s = this._state;

    // Text fields
    this._elements.liveBadge.textContent = s.liveBadgeText;
    this._elements.subtitleBar.textContent = s.subtitle;
    this._elements.breakingTextEl.textContent = s.breakingText;
    this._elements.newsTextEl.textContent = s.newsText;
    this._elements.categoryLabel.textContent = s.categoryLabel;
    this._elements.headlineBar.textContent = s.headline;
    this._elements.tickerText.textContent = s.tickerText;

    // Color fields
    if (s.liveBadgeColor) this.style.setProperty("--live-badge-color", s.liveBadgeColor);
    if (s.subtitleBarColor) this.style.setProperty("--subtitle-bar-color", s.subtitleBarColor);
    if (s.breakingBgColor) this.style.setProperty("--breaking-bg-color", s.breakingBgColor);
    if (s.newsBgColor) this.style.setProperty("--news-bg-color", s.newsBgColor);
    if (s.categoryColor) this.style.setProperty("--category-color", s.categoryColor);
    if (s.headlineColor) this.style.setProperty("--headline-color", s.headlineColor);
    if (s.tickerBgColor) this.style.setProperty("--ticker-bg-color", s.tickerBgColor);

    // Reset ticker width measurement for scrolling calculation
    this._tickerWidth = 0;
  }

  _resolveTargetStep(params) {
    const stepCount = 1;
    const goto = params?.goto;
    const delta = typeof params?.delta === "number" ? params.delta : 1;

    if (typeof goto === "number") {
      return Math.max(0, Math.min(goto, stepCount));
    }

    const current = typeof this._currentStep === "number" ? this._currentStep : -1;
    const target = current + delta;

    return Math.max(0, Math.min(target, stepCount));
  }

  _cancelAnimations() {
    this._animations.forEach((a) => a.cancel());
    this._animations = [];
  }

  _measureTickerWidth() {
    if (this._tickerWidth <= 0) {
      const el = this._elements.tickerText;
      this._tickerWidth = el.scrollWidth || el.offsetWidth || 1600;
    }
    return this._tickerWidth;
  }

  _setFrame(seconds) {
    const {
      scene,
      logoBug,
      sidePanel,
      lowerThird,
      categoryRow,
      headlineRow,
      tickerRow,
      tickerText,
    } = this._elements;
    const duration = 11;

    // ── Hidden state ──
    if (this._currentStep === 0) {
      scene.style.opacity = "0";
      sidePanel.style.transform = "translateX(-100%)";
      headlineRow.style.transform = "translateX(-110%)";
      categoryRow.style.opacity = "0";
      categoryRow.style.transform = "translateY(10px)";
      tickerRow.style.transform = "scaleX(0)";
      tickerText.style.transform = "translateX(100%)";
      this._isVisible = false;
      return;
    }

    scene.style.opacity = "1";
    this._isVisible = true;

    // Logo bug is always visible when scene is active
    logoBug.style.opacity = "1";

    // ── Phase 1: Side panel + Headline slide in (0 - 0.3s) ──
    const slideProgress = easeOutCubic(clamp(seconds / 0.3, 0, 1));
    sidePanel.style.transform = `translateX(${(-100 + 100 * slideProgress).toFixed(1)}%)`;
    headlineRow.style.transform = `translateX(${(-110 + 110 * slideProgress).toFixed(1)}%)`;

    // ── Phase 2: Category label fade in (0.3 - 0.7s) ──
    const catProgress = easeOutCubic(clamp((seconds - 0.3) / 0.4, 0, 1));
    categoryRow.style.opacity = String(catProgress);
    categoryRow.style.transform = `translateY(${(10 - 10 * catProgress).toFixed(1)}px)`;

    // ── Phase 3: Ticker bar expand (0.7 - 1.2s) ──
    const tickerExpandProgress = easeOutCubic(clamp((seconds - 0.7) / 0.5, 0, 1));
    tickerRow.style.transform = `scaleX(${tickerExpandProgress.toFixed(4)})`;

    // ── Phase 4: Ticker text scroll (1.2s onward) ──
    if (seconds >= 1.2) {
      const tickerW = this._measureTickerWidth();
      const containerW = 1920 - 55 - 60; // full width minus side panel minus right margin
      const scrollElapsed = seconds - 1.2;
      const scrollSpeed = 120; // pixels per second
      const totalScrollDist = tickerW + containerW;
      // Start from right edge, scroll left
      const offset = containerW - scrollElapsed * scrollSpeed;
      // Loop the scroll
      const loopedOffset =
        ((offset % totalScrollDist) + totalScrollDist) % totalScrollDist -
        tickerW;
      tickerText.style.transform = `translateX(${loopedOffset.toFixed(1)}px)`;
    } else {
      // Before ticker starts, hide text off to the right
      tickerText.style.transform = `translateX(${1920}px)`;
    }
  }
}

export default BreakingNewsV2Graphic;
