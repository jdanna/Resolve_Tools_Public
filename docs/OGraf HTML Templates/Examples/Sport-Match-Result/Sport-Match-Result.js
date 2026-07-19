
const DEFAULT_STATE = {
  title: "MATCH RESULT",
  scale: 1.0,
  titleColor: "#1a1a1a",
  teamAName: "VANGUARD BEASTS",
  teamAScore: 21,
  teamACaption: "VANGUARD BEASTS WIN GOLD",
  showTeamACaption: true,
  teamAColor: "#1a5fb4",
  teamBName: "VANTA CLUB",
  teamBScore: 19,
  teamBCaption: "",
  showTeamBCaption: false,
  teamBColor: "#b91c1c",
};

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

const STYLE_TEXT = `
:host {
  position: absolute;
  inset: 0;
  display: block;
  pointer-events: none;
  font-family: "Arial", "Helvetica Neue", sans-serif;
  --title-color: #1a1a1a;
  --team-a-color: #1a5fb4;
  --team-b-color: #b91c1c;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

.scene {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  opacity: 0;
  will-change: opacity;
}

/* ── Title ── */
.title {
  font-size: 90px;
  font-weight: 900;
  color: var(--title-color);
  text-transform: uppercase;
  letter-spacing: -0.02em;
  margin-bottom: 40px;
  will-change: opacity, transform;
  font-family: "Impact", "Arial Black", "Arial", sans-serif;
}

/* ── Card Container ── */
.card {
  display: flex;
  flex-direction: column;
  width: 620px;
  gap: 0;
}

/* ── Team Row ── */
.team-row {
  display: flex;
  height: 80px;
  overflow: hidden;
  will-change: transform, opacity;
}

.team-name-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 30px;
  color: #fff;
  font-weight: 800;
  font-size: 30px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  white-space: nowrap;
}

.team-name-section.team-a {
  background: linear-gradient(to right, #0a1628, var(--team-a-color), #6da4e0);
}

.team-name-section.team-b {
  background: linear-gradient(to right, #3d0a0a, var(--team-b-color), #e06d6d);
}

.score-section {
  width: 130px;
  min-width: 130px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  color: #1a1a1a;
  font-weight: 900;
  font-size: 62px;
  letter-spacing: -0.02em;
  font-family: "Impact", "Arial Black", "Arial", sans-serif;
  will-change: opacity;
}

/* ── Caption Row ── */
.caption-row {
  display: flex;
  align-items: center;
  height: 36px;
  background: rgba(220, 240, 235, 0.7);
  padding: 0 16px;
  gap: 8px;
  will-change: opacity, transform;
}

.caption-icon {
  font-size: 18px;
  line-height: 1;
}

.caption-text {
  font-size: 16px;
  font-weight: 700;
  color: #3a5a50;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

/* ── Gap between teams ── */
.team-gap {
  height: 50px;
}
`;

class MatchResultGraphic extends HTMLElement {
  constructor() {
    super();
    this._state = { ...DEFAULT_STATE };
    this._isVisible = false;
    this._currentStep = 1;
    this._animations = [];

    const root = this.attachShadow({ mode: "open" });
    const style = document.createElement("style");
    style.textContent = STYLE_TEXT;

    // Scene
    const scene = document.createElement("div");
    scene.className = "scene";

    // Title
    const title = document.createElement("div");
    title.className = "title";

    // Card container
    const card = document.createElement("div");
    card.className = "card";

    // Team A row
    const teamARow = document.createElement("div");
    teamARow.className = "team-row";

    const teamANameSection = document.createElement("div");
    teamANameSection.className = "team-name-section team-a";

    const teamAScoreSection = document.createElement("div");
    teamAScoreSection.className = "score-section";

    teamARow.append(teamANameSection, teamAScoreSection);

    // Team A caption row
    const teamACaptionRow = document.createElement("div");
    teamACaptionRow.className = "caption-row";

    const teamACaptionIcon = document.createElement("span");
    teamACaptionIcon.className = "caption-icon";
    teamACaptionIcon.textContent = "\uD83C\uDFC6";

    const teamACaptionText = document.createElement("span");
    teamACaptionText.className = "caption-text";

    teamACaptionRow.append(teamACaptionIcon, teamACaptionText);

    // Gap
    const teamGap = document.createElement("div");
    teamGap.className = "team-gap";

    // Team B row
    const teamBRow = document.createElement("div");
    teamBRow.className = "team-row";

    const teamBNameSection = document.createElement("div");
    teamBNameSection.className = "team-name-section team-b";

    const teamBScoreSection = document.createElement("div");
    teamBScoreSection.className = "score-section";

    teamBRow.append(teamBNameSection, teamBScoreSection);

    // Team B caption row
    const teamBCaptionRow = document.createElement("div");
    teamBCaptionRow.className = "caption-row";

    const teamBCaptionIcon = document.createElement("span");
    teamBCaptionIcon.className = "caption-icon";
    teamBCaptionIcon.textContent = "\uD83C\uDFC6";

    const teamBCaptionText = document.createElement("span");
    teamBCaptionText.className = "caption-text";

    teamBCaptionRow.append(teamBCaptionIcon, teamBCaptionText);

    card.append(teamARow, teamACaptionRow, teamGap, teamBRow, teamBCaptionRow);
    scene.append(title, card);
    root.append(style, scene);

    this._elements = {
      scene,
      title,
      card,
      teamARow,
      teamANameSection,
      teamAScoreSection,
      teamACaptionRow,
      teamACaptionText,
      teamBRow,
      teamBNameSection,
      teamBScoreSection,
      teamBCaptionRow,
      teamBCaptionText,
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

    this._elements.title.textContent = s.title;

    // Team A
    this._elements.teamANameSection.textContent = s.teamAName;
    this._elements.teamAScoreSection.textContent = String(s.teamAScore);
    this._elements.teamACaptionText.textContent = s.teamACaption;
    this._elements.teamACaptionRow.style.display = s.showTeamACaption ? "flex" : "none";

    // Team B
    this._elements.teamBNameSection.textContent = s.teamBName;
    this._elements.teamBScoreSection.textContent = String(s.teamBScore);
    this._elements.teamBCaptionText.textContent = s.teamBCaption;
    this._elements.teamBCaptionRow.style.display = s.showTeamBCaption ? "flex" : "none";

    // Scale
    const scale = s.scale != null ? s.scale : 1.0;
    this._elements.scene.style.transform = `scale(${scale})`;

    // Colors
    if (s.titleColor) this.style.setProperty("--title-color", s.titleColor);
    if (s.teamAColor) this.style.setProperty("--team-a-color", s.teamAColor);
    if (s.teamBColor) this.style.setProperty("--team-b-color", s.teamBColor);
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

  _setFrame(seconds) {
    const {
      scene,
      title,
      teamARow,
      teamAScoreSection,
      teamACaptionRow,
      teamBRow,
      teamBScoreSection,
      teamBCaptionRow,
    } = this._elements;
    const duration = 5;

    // ── Hidden state ──
    if (this._currentStep === 0) {
      scene.style.opacity = "0";
      title.style.opacity = "0";
      title.style.transform = "translateY(20px)";
      teamARow.style.opacity = "0";
      teamARow.style.transform = "translateX(-60px)";
      teamAScoreSection.style.opacity = "0";
      teamACaptionRow.style.opacity = "0";
      teamACaptionRow.style.transform = "translateY(-8px)";
      teamBRow.style.opacity = "0";
      teamBRow.style.transform = "translateX(-60px)";
      teamBScoreSection.style.opacity = "0";
      teamBCaptionRow.style.opacity = "0";
      teamBCaptionRow.style.transform = "translateY(-8px)";
      this._isVisible = false;
      return;
    }

    scene.style.opacity = "1";
    this._isVisible = true;

    // ── Phase 1: Title fade in (0 - 0.3s) ──
    const titleProgress = easeOutCubic(clamp(seconds / 0.3, 0, 1));
    title.style.opacity = String(titleProgress);
    title.style.transform = `translateY(${(20 - 20 * titleProgress).toFixed(1)}px)`;

    // ── Phase 2: Team bars slide in (0.1 - 0.5s) ──
    const teamABarProgress = easeOutBack(clamp((seconds - 0.1) / 0.4, 0, 1));
    teamARow.style.opacity = String(clamp(teamABarProgress, 0, 1));
    teamARow.style.transform = `translateX(${(-60 + 60 * teamABarProgress).toFixed(1)}px)`;

    const teamBBarProgress = easeOutBack(clamp((seconds - 0.2) / 0.4, 0, 1));
    teamBRow.style.opacity = String(clamp(teamBBarProgress, 0, 1));
    teamBRow.style.transform = `translateX(${(-60 + 60 * teamBBarProgress).toFixed(1)}px)`;

    // ── Phase 3: Scores fade in (0.5 - 1.0s) ──
    const teamAScoreProgress = easeOutCubic(clamp((seconds - 0.5) / 0.5, 0, 1));
    teamAScoreSection.style.opacity = String(teamAScoreProgress);

    const teamBScoreProgress = easeOutCubic(clamp((seconds - 0.65) / 0.5, 0, 1));
    teamBScoreSection.style.opacity = String(teamBScoreProgress);

    // ── Phase 4: Captions fade in (1.0 - 1.4s) ──
    const teamACaptionProgress = easeOutCubic(clamp((seconds - 1.0) / 0.4, 0, 1));
    teamACaptionRow.style.opacity = String(teamACaptionProgress);
    teamACaptionRow.style.transform = `translateY(${(-8 + 8 * teamACaptionProgress).toFixed(1)}px)`;

    const teamBCaptionProgress = easeOutCubic(clamp((seconds - 1.1) / 0.4, 0, 1));
    teamBCaptionRow.style.opacity = String(teamBCaptionProgress);
    teamBCaptionRow.style.transform = `translateY(${(-8 + 8 * teamBCaptionProgress).toFixed(1)}px)`;
  }
}

export default MatchResultGraphic;
