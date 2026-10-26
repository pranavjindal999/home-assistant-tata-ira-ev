// Tata iRA.ev dashboard card. One card for every control and sensor on the car.

const MARK = `<img src="/tata_ira/curvv.png?v=0.7.7" alt="">`;

const UNIQUE_ROLE = {
  battery: "battery",
  charge_time: "chargeTime",
  charging: "charging",
  connected: "connected",
  front_left_tyre: "tyreFl",
  front_right_tyre: "tyreFr",
  back_left_tyre: "tyreBl",
  back_right_tyre: "tyreBr",
  tyre_pressure: "tyreLow",
  range: "range",
  odometer: "odometer",
  aux_battery: "aux",
  service_due: "serviceDays",
  service_distance: "serviceKm",
  speed: "speed",
  charger: "charger",
  aux_battery_low: "auxLow",
  warning: "warning",
  front_left_door: "doorFl",
  front_right_door: "doorFr",
  rear_left_door: "doorRl",
  rear_right_door: "doorRr",
  bonnet: "bonnet",
  tailgate: "tailgate",
  ignition: "ignition",
  high_beam: "highBeam",
  low_beam: "lowBeam",
  ac: "ac",
  approach_lights: "approach",
  headlights: "headlights",
  hazard_lights: "hazard",
  horn: "horn",
  refresh: "refresh",
  lock: "lock",
  ac_minutes: "acMinutes",
  location: "location",
};

const SLUG_ROLE = {
  battery: "battery",
  charge_time_remaining: "chargeTime",
  charging: "charging",
  connected: "connected",
  front_left_tyre: "tyreFl",
  front_right_tyre: "tyreFr",
  back_left_tyre: "tyreBl",
  back_right_tyre: "tyreBr",
  tyre_pressure: "tyreLow",
  range: "range",
  odometer: "odometer",
  "12v_battery": "aux",
  service_due: "serviceDays",
  service_distance: "serviceKm",
  speed: "speed",
  charger_connected: "charger",
  "12v_battery_low": "auxLow",
  warning: "warning",
  front_left_door: "doorFl",
  front_right_door: "doorFr",
  rear_left_door: "doorRl",
  rear_right_door: "doorRr",
  bonnet: "bonnet",
  tailgate: "tailgate",
  ignition: "ignition",
  high_beam: "highBeam",
  low_beam: "lowBeam",
  air_conditioning: "ac",
  air_conditioning_duration: "acMinutes",
  approach_lights: "approach",
  headlights: "headlights",
  hazard_lights: "hazard",
  horn: "horn",
  refresh: "refresh",
  lock: "lock",
  location: "location",
};

const SLUGS = Object.entries(SLUG_ROLE).sort((a, b) => b[0].length - a[0].length);

const STYLE = `
:host { display: block; }
ha-card {
  display: block;
  container-type: inline-size;
  container-name: ira;
}
.wrap {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  color: var(--primary-text-color);
}
.board {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.main, .side {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}
header { display: flex; align-items: flex-start; gap: 12px; }
.who { display: flex; align-items: center; gap: 10px; min-width: 0; }
.mark {
  width: 92px;
  height: 38px;
  flex: none;
  display: block;
}
.mark img { width: 100%; height: 100%; object-fit: contain; display: block; }
.name { font-size: 16px; font-weight: 600; line-height: 1.2; }
.sub { margin-top: 2px; color: var(--secondary-text-color); font-size: 13px; }
.tools { margin-left: auto; display: flex; align-items: center; gap: 8px; flex: none; }
.conn { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--secondary-text-color); }
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--disabled-text-color, var(--secondary-text-color)); }
.dot.on { background: var(--success-color, #2e7d32); }
.dot.off { background: var(--error-color, #c62828); }
.icon-btn, .tile, .tile-hit, .stepper button, .stat, .chip, .location, .choose {
  font: inherit;
  color: inherit;
  cursor: pointer;
}
.icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid var(--divider-color);
  background: transparent;
  display: grid;
  place-items: center;
}
.hero { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 16px; align-items: end; }
.soc-btn, .range-btn {
  border: 0;
  background: transparent;
  padding: 0;
  text-align: left;
  font: inherit;
  color: inherit;
  cursor: pointer;
}
.soc-value { font-size: 42px; font-weight: 600; letter-spacing: -0.04em; line-height: 0.95; }
.soc-value span { font-size: 20px; font-weight: 500; margin-left: 1px; }
.bar { height: 8px; border-radius: 99px; background: color-mix(in srgb, var(--primary-text-color) 12%, transparent); overflow: hidden; margin-top: 10px; }
.bar > div { height: 100%; border-radius: 99px; background: var(--primary-color); }
.bar.low > div { background: var(--error-color, #c62828); }
.meta { margin-top: 8px; font-size: 13px; color: var(--secondary-text-color); }
.range-btn { text-align: right; }
.range-value { font-size: 28px; font-weight: 600; letter-spacing: -0.03em; line-height: 1; }
.range-unit { margin-top: 4px; font-size: 12px; color: var(--secondary-text-color); }
.banner {
  border-radius: 12px;
  padding: 10px 12px;
  background: color-mix(in srgb, var(--error-color, #c62828) 12%, transparent);
  color: var(--error-color, #c62828);
  font-size: 14px;
  font-weight: 500;
}
.controls { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
.tile {
  min-height: 76px;
  border-radius: 14px;
  border: 1px solid var(--divider-color);
  background: transparent;
  padding: 8px 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 12px;
  line-height: 1.2;
  text-align: center;
  min-width: 0;
}
.tile span { max-width: 100%; }
.tile.on {
  background: color-mix(in srgb, var(--primary-color) 16%, transparent);
  border-color: color-mix(in srgb, var(--primary-color) 42%, var(--divider-color));
  color: var(--primary-color);
}
.tile.alert {
  background: color-mix(in srgb, var(--error-color, #c62828) 12%, transparent);
  border-color: color-mix(in srgb, var(--error-color, #c62828) 40%, var(--divider-color));
  color: var(--error-color, #c62828);
}
.tile.climate { padding: 0; gap: 0; justify-content: stretch; }
.tile-hit {
  flex: 1;
  width: 100%;
  border: 0;
  background: transparent;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px 6px 4px;
  font-size: 12px;
}
.hint { color: var(--secondary-text-color); font-size: 11px; }
.tile.on .hint, .tile.alert .hint { color: inherit; opacity: 0.8; }
.stepper {
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr) 32px;
  align-items: center;
  width: 100%;
  box-sizing: border-box;
  padding: 0 6px 8px;
  font-size: 12px;
}
.stepper span { text-align: center; }
.stepper button, .icon-btn {
  border: 0;
}
.stepper button {
  height: 28px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--primary-text-color) 8%, transparent);
  color: inherit;
}
.stepper button:disabled { opacity: 0.35; cursor: default; }
ha-icon { --mdc-icon-size: 22px; }
.icon-btn ha-icon { --mdc-icon-size: 18px; }
.section { display: flex; flex-direction: column; gap: 8px; }
h3 {
  margin: 0;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--secondary-text-color);
}
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(132px, 1fr)); gap: 4px; }
.stat {
  border: 0;
  background: transparent;
  border-radius: 10px;
  padding: 8px;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.stat .label { font-size: 12px; color: var(--secondary-text-color); }
.stat .value { font-size: 16px; font-weight: 500; }
.car-widget { width: min(100%, 420px); margin: 0 auto; }
.car-stage {
  display: grid;
  grid-template-columns: 68px minmax(0, 1fr) 68px;
  grid-template-rows: auto auto;
  align-items: center;
  column-gap: 4px;
}
.car-art { grid-column: 2; grid-row: 1 / span 2; position: relative; min-width: 0; }
.car-svg { width: 100%; height: auto; display: block; aspect-ratio: 240 / 460; }
.car-svg .shadow { fill: color-mix(in srgb, var(--primary-text-color) 16%, transparent); }
.car-svg .body { fill: #9aafd4; }
.car-svg .cladding { fill: #1b1e24; }
.car-svg .glass { fill: #243044; }
.car-svg .panel { fill: #8ea3cb; stroke: #1b2433; stroke-width: 1.25; }
.car-svg .panel.open { fill: #e35d5d; }
.car-svg .door { transform-box: fill-box; transition: transform 0.35s ease; }
.car-svg .door.fl, .car-svg .door.rl { transform-origin: 100% 0%; }
.car-svg .door.fr, .car-svg .door.rr { transform-origin: 0% 0%; }
.car-svg .door.fl.open, .car-svg .door.rl.open { transform: rotate(-58deg); }
.car-svg .door.fr.open, .car-svg .door.rr.open { transform: rotate(58deg); }
.car-svg .bonnet, .car-svg .tail { transform-box: fill-box; transition: transform 0.35s ease; }
.car-svg .bonnet { transform-origin: 50% 100%; }
.car-svg .bonnet.open { transform: translateY(-10px); }
.car-svg .tail { transform-origin: 50% 0%; }
.car-svg .tail.open { transform: translateY(12px); }
.car-svg .wheel { fill: #2a2e36; }
.car-svg .hub { fill: #d7dee8; }
.car-svg .wheel.low { fill: #8d2f2f; }
.car-svg .lamp { fill: #d5dce8; }
.car-svg .lamp.lit { fill: #ffe08a; }
.car-svg .lamp.high { fill: #fff7d6; }
.car-svg .port { fill: #2a2e36; }
.car-svg .port.on { fill: #3dd68c; }
.reading, .zone {
  font: inherit;
  color: inherit;
  cursor: pointer;
  border: 0;
  background: transparent;
  padding: 0;
}
.reading {
  font-size: 12px;
  font-weight: 600;
  line-height: 1.25;
  text-align: center;
  min-width: 0;
}
.reading .where { display: block; font-size: 10px; font-weight: 500; color: var(--secondary-text-color); }
.reading.low { color: var(--error-color, #c62828); }
.reading.fl { grid-column: 1; grid-row: 1; }
.reading.fr { grid-column: 3; grid-row: 1; }
.reading.bl { grid-column: 1; grid-row: 2; }
.reading.br { grid-column: 3; grid-row: 2; }
.zone { position: absolute; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
span.chip { cursor: default; }
.chip {
  border-radius: 999px;
  border: 1px solid var(--divider-color);
  background: transparent;
  padding: 5px 10px;
  font-size: 12px;
}
.chip.on {
  background: color-mix(in srgb, var(--primary-color) 14%, transparent);
  border-color: transparent;
  color: var(--primary-color);
}
.chip.alert {
  background: color-mix(in srgb, var(--error-color, #c62828) 12%, transparent);
  border-color: transparent;
  color: var(--error-color, #c62828);
}
.map-slot {
  height: 220px;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid var(--divider-color);
  background: color-mix(in srgb, var(--primary-text-color) 4%, transparent);
}
.map-slot ha-map,
.map,
.map-frame {
  display: block;
  width: 100%;
  height: 100%;
  border: 0;
}
.choose {
  width: 100%;
  border-radius: 10px;
  border: 1px solid var(--divider-color);
  background: var(--card-background-color);
  padding: 8px 10px;
}
.busy { opacity: 0.55; }
.empty { color: var(--secondary-text-color); font-size: 14px; padding: 8px 0; }
button:focus-visible, .stat:focus-visible, .chip:focus-visible, .reading:focus-visible, .zone:focus-visible {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}
@media (hover: hover) {
  .tile:hover, .stat:hover, .chip:hover, .reading:hover, .icon-btn:hover {
    background: color-mix(in srgb, var(--primary-text-color) 6%, transparent);
  }
  .tile.on:hover { background: color-mix(in srgb, var(--primary-color) 22%, transparent); }
}
@container ira (max-width: 340px) {
  .controls { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .soc-value { font-size: 36px; }
  .range-value { font-size: 24px; }
  .map-slot { height: 180px; }
}
@container ira (min-width: 560px) {
  .board {
    display: grid;
    grid-template-columns: minmax(0, 1.15fr) minmax(240px, 0.85fr);
    gap: 16px 28px;
    align-items: start;
  }
  .main { grid-column: 1; grid-row: 1; }
  .side { grid-column: 2; grid-row: 1 / span 2; }
  .facts { grid-column: 1; grid-row: 2; }
  .map-slot { height: 280px; }
}
@container ira (min-width: 1040px) {
  .board {
    grid-template-columns: minmax(260px, 0.95fr) minmax(280px, 1.15fr) minmax(250px, 0.9fr);
  }
  .main { grid-column: 1; grid-row: 1; }
  .facts { grid-column: 2; grid-row: 1; }
  .side { grid-column: 3; grid-row: 1; }
  .facts .stats { grid-template-columns: 1fr 1fr; }
  .board:not(:has(.facts)) { grid-template-columns: minmax(0, 1.1fr) minmax(250px, 0.9fr); }
  .board:not(:has(.facts)) .side { grid-column: 2; }
  .board:not(:has(.side)) { grid-template-columns: minmax(260px, 0.8fr) minmax(0, 1.2fr); }
  .board:not(:has(.side)) .facts { grid-column: 2; }
}
`;

function esc(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function roleForUnique(vehicleId, uniqueId) {
  if (!vehicleId || typeof uniqueId !== "string") return null;
  const prefix = `${vehicleId}_`;
  if (!uniqueId.startsWith(prefix)) return null;
  return UNIQUE_ROLE[uniqueId.slice(prefix.length)] || null;
}

function roleForEntityId(entityId) {
  const objectId = String(entityId || "").split(".")[1] || "";
  for (const [slug, role] of SLUGS) {
    if (objectId === slug || objectId.endsWith(`_${slug}`)) return role;
  }
  return null;
}

function isBlank(state) {
  return !state || ["unavailable", "unknown", "none", ""].includes(state.state);
}

function isOn(state) {
  return state?.state === "on" || state?.state === "locked";
}

function display(state) {
  if (isBlank(state)) return "—";
  const unit = state.attributes?.unit_of_measurement;
  return unit ? `${state.state} ${unit}` : state.state;
}

function splitValue(state) {
  if (isBlank(state)) return { value: "—", unit: "" };
  return {
    value: state.state,
    unit: state.attributes?.unit_of_measurement || "",
  };
}

function identifiersOf(device) {
  try {
    const ids = device && device.identifiers;
    if (!ids) return [];
    const list = Array.isArray(ids)
      ? ids
      : typeof ids !== "string" && typeof ids[Symbol.iterator] === "function"
        ? Array.from(ids)
        : [];
    return list.filter((id) => Array.isArray(id));
  } catch (_err) {
    return [];
  }
}

function devicesFrom(hass, cached) {
  const source = hass.devices ? Object.values(hass.devices) : cached || [];
  return source.filter((device) => {
    try {
      if (!device || typeof device !== "object") return false;
      const match = identifiersOf(device).some((id) => id[0] === "tata_ira");
      return match || (device.manufacturer === "Tata Motors" && device.model === "iRA.ev");
    } catch (_err) {
      return false;
    }
  });
}

function entriesFrom(hass, registry) {
  if (registry) return registry;
  if (!hass.entities) return [];
  return Object.values(hass.entities);
}

function indexCar(device, entries, states) {
  const ident = identifiersOf(device).find((id) => Array.isArray(id) && id[0] === "tata_ira");
  const vehicleId = ident ? ident[1] : null;
  const ranked = [];
  const list = Array.isArray(entries) ? entries : [];
  for (const entry of list) {
    if (!entry || entry.device_id !== device.id) continue;
    if (entry.disabled_by || entry.hidden_by) continue;
    const exact = roleForUnique(vehicleId, entry.unique_id);
    const role = exact || roleForEntityId(entry.entity_id);
    if (!role) continue;
    ranked.push({ role, exact: Boolean(exact), entityId: entry.entity_id });
  }
  ranked.sort((a, b) => Number(b.exact) - Number(a.exact));
  const map = {};
  for (const item of ranked) {
    if (!map[item.role]) map[item.role] = states[item.entityId];
  }
  return map;
}

function icon(name) {
  return `<ha-icon icon="${esc(name)}"></ha-icon>`;
}

class TataIraCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._busy = new Set();
    this._picked = null;
  }

  static getStubConfig() {
    return {};
  }

  setConfig(config) {
    if (!config || Array.isArray(config) || typeof config !== "object") {
      throw new Error("Invalid card configuration");
    }
    this._config = config;
    if (this._hass) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    try {
      const signature = this._signature();
      if (signature !== this._signatureValue) {
        this._signatureValue = signature;
        this._render();
      }
    } catch (err) {
      console.error("Tata iRA.ev card", err);
      this._showFailure();
    }
    if (!this._registryRequested) {
      this._registryRequested = true;
      try {
        this._loadRegistry();
      } catch (err) {
        console.error("Tata iRA.ev card", err);
      }
    }
  }

  getCardSize() {
    return 10;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 4, rows: "auto" };
  }

  _signature() {
    if (!this._hass) return "";
    const device = this._device();
    const entries = entriesFrom(this._hass, this._registry);
    const map = device ? indexCar(device, entries, this._hass.states) : {};
    const bits = Object.entries(map).map(
      ([role, state]) =>
        `${role}:${state?.state}:${state?.last_updated}:${state?.attributes?.unit_of_measurement || ""}`
    );
    bits.push([...this._busy].sort().join(","));
    bits.push(this._picked || "");
    bits.push(this._config.entity || "");
    return bits.join("|");
  }

  async _loadRegistry() {
    try {
      const [devices, entities] = await Promise.all([
        this._hass.devices
          ? null
          : this._hass.callWS({ type: "config/device_registry/list" }),
        this._hass.callWS({ type: "config/entity_registry/list" }),
      ]);
      if (devices) this._devices = devices;
      this._registry = entities;
    } catch (_err) {
      this._registry = null;
    }
    this._signatureValue = null;
    if (this._hass) this.hass = this._hass;
  }

  _device() {
    const devices = devicesFrom(this._hass, this._devices);
    if (!devices.length) return null;
    const wanted = this._config.entity;
    if (wanted && this._hass.entities?.[wanted]?.device_id) {
      const found = devices.find((device) => device.id === this._hass.entities[wanted].device_id);
      if (found) return found;
    }
    if (this._picked) {
      const found = devices.find((device) => device.id === this._picked);
      if (found) return found;
    }
    return devices[0];
  }

  _render() {
    try {
      this._renderBody();
    } catch (err) {
      console.error("Tata iRA.ev card", err);
      this._showFailure();
    }
  }

  _showFailure() {
    try {
      const root = this.shadowRoot;
      if (!root) return;
      let body = root.getElementById("body");
      if (!body) {
        root.innerHTML = `<div id="body"></div>`;
        body = root.getElementById("body");
      }
      if (!body.querySelector("ha-card")) {
        body.innerHTML = `<ha-card><div class="wrap"><p class="empty">The Tata iRA.ev card hit an error. Reload the page.</p></div></ha-card>`;
      }
    } catch (_err) {
      /* Leave the last good render in place. */
    }
  }

  _renderBody() {
    if (!this.shadowRoot.querySelector("#body")) {
      this.shadowRoot.innerHTML = `<style>${STYLE}</style><div id="body"></div>`;
      this.shadowRoot.getElementById("body").addEventListener("click", (event) => {
        const target = event.target && event.target.closest ? event.target.closest("[data-action]") : null;
        if (!target || !this.shadowRoot.contains(target) || target.dataset.action === "pick") return;
        event.preventDefault();
        event.stopPropagation();
        this._handle(target);
      });
      this.shadowRoot.getElementById("body").addEventListener("change", (event) => {
        const select = event.target && event.target.closest ? event.target.closest("[data-action='pick']") : null;
        if (!select) return;
        this._picked = select.value;
        this._signatureValue = null;
        this._render();
      });
    }
    const body = this.shadowRoot.getElementById("body");
    const devices = this._hass ? devicesFrom(this._hass, this._devices) : [];
    if (!devices.length) {
      body.innerHTML = `<ha-card><div class="wrap"><p class="empty">Add the Tata iRA.ev integration, then this card fills in from the car.</p></div></ha-card>`;
      return;
    }
    const device = this._device();
    const entries = entriesFrom(this._hass, this._registry);
    const map = indexCar(device, entries, this._hass.states);
    body.innerHTML = `<ha-card><div class="wrap">${this._html(device, devices, map)}</div></ha-card>`;
    this._mountCar(map);
    this._mountMap();
  }

  _html(device, devices, map) {
    const name = device.name_by_user || device.name || "Tata iRA.ev";
    const parts = [];
    if (devices.length > 1 && !this._config.entity) {
      const options = devices
        .map((item) => {
          const label = item.name_by_user || item.name || "Tata iRA.ev";
          const selected = item.id === device.id ? " selected" : "";
          return `<option value="${esc(item.id)}"${selected}>${esc(label)}</option>`;
        })
        .join("");
      parts.push(`<select class="choose" data-action="pick" aria-label="Car">${options}</select>`);
    }
    parts.push(this._header(name, map));
    parts.push(this._banner(map));
    parts.push(this._hero(map));
    parts.push(`<div class="car-slot"></div>`);
    const controls = this._controls(map);
    const stats = this._stats(map);
    const location =
      map.location && !isBlank(map.location)
        ? `<section class="section map-block"><h3>Location</h3><div class="map-slot" data-entity="${esc(map.location.entity_id)}"></div></section>`
        : "";
    const side = [location, this._chips(map)].filter(Boolean).join("");
    const main = controls ? `<div class="main">${controls}</div>` : "";
    const aside = side ? `<div class="side">${side}</div>` : "";
    parts.push(`<div class="board">${main}${stats}${aside}</div>`);
    return parts.filter(Boolean).join("");
  }

  _mountCar(map) {
    const slot = this.shadowRoot.querySelector(".car-slot");
    if (!slot) return;
    try {
      slot.innerHTML = this._car(map);
    } catch (err) {
      console.error("Tata iRA.ev card", err);
      slot.replaceChildren();
    }
  }

  _mountMap() {
    const slot = this.shadowRoot.querySelector(".map-slot");
    if (!slot) return;
    const entityId = slot.dataset.entity;
    const state = this._hass?.states?.[entityId];
    const lat = Number(state?.attributes?.latitude);
    const lon = Number(state?.attributes?.longitude);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;
    const pad = 0.008;
    const bbox = [lon - pad, lat - pad, lon + pad, lat + pad].map((n) => n.toFixed(5)).join(",");
    const src = `https://www.openstreetmap.org/export/embed.html?bbox=${encodeURIComponent(bbox)}&layer=mapnik&marker=${encodeURIComponent(`${lat.toFixed(5)},${lon.toFixed(5)}`)}`;
    let frame = this._mapFrame;
    if (!frame) {
      frame = document.createElement("iframe");
      frame.className = "map-frame";
      frame.title = "Location";
      frame.loading = "lazy";
      frame.referrerPolicy = "no-referrer-when-downgrade";
      this._mapFrame = frame;
    }
    if (frame.getAttribute("data-src") !== src) {
      frame.setAttribute("data-src", src);
      frame.src = src;
    }
    if (frame.parentElement !== slot) slot.replaceChildren(frame);
  }

  _header(name, map) {
    const connected = map.connected;
    const online = isOn(connected);
    const dot = !connected ? "" : `<span class="dot ${online ? "on" : "off"}"></span>`;
    const label = !connected ? "" : online ? "Connected" : "Not connected";
    const bits = [];
    if (map.lock && !isBlank(map.lock)) bits.push(map.lock.state === "locked" ? "Locked" : "Unlocked");
    if (map.speed && !isBlank(map.speed) && Number(map.speed.state) > 0) bits.push(display(map.speed));
    const refresh = map.refresh
      ? `<button class="icon-btn ${this._busy.has(map.refresh.entity_id) ? "busy" : ""}" data-action="press" data-entity="${esc(map.refresh.entity_id)}" aria-label="Refresh">${icon("mdi:refresh")}</button>`
      : "";
    return `<header>
      <div class="who"><span class="mark">${MARK}</span><div><div class="name">${esc(name)}</div><div class="sub">${esc(bits.join(" · ") || "Tata iRA.ev")}</div></div></div>
      <div class="tools">${refresh}<div class="conn">${dot}<span>${esc(label)}</span></div></div>
    </header>`;
  }

  _banner(map) {
    const issues = [];
    if (isOn(map.warning)) issues.push("Warning");
    if (isOn(map.tyreLow)) issues.push("Tyre pressure low");
    if (isOn(map.auxLow)) issues.push("12V battery low");
    for (const [role, label] of [
      ["doorFl", "Front left door open"],
      ["doorFr", "Front right door open"],
      ["doorRl", "Rear left door open"],
      ["doorRr", "Rear right door open"],
      ["bonnet", "Bonnet open"],
      ["tailgate", "Tailgate open"],
    ]) {
      if (isOn(map[role])) issues.push(label);
    }
    if (!issues.length) return "";
    return `<div class="banner">${esc(issues.join(" · "))}</div>`;
  }

  _hero(map) {
    const battery = map.battery;
    const percent = battery && !isBlank(battery) ? Number(battery.state) : null;
    const width = percent == null || Number.isNaN(percent) ? 0 : Math.max(0, Math.min(100, percent));
    const low = percent != null && percent <= 20;
    const shown = percent == null || Number.isNaN(percent) ? "—" : `${Math.round(percent)}`;
    let meta = "Not charging";
    if (isOn(map.charging)) {
      meta = map.chargeTime && !isBlank(map.chargeTime) ? `Charging · ${display(map.chargeTime)} left` : "Charging";
    } else if (isOn(map.charger)) {
      meta = "Plugged in";
    }
    const range = splitValue(map.range);
    const batteryId = battery ? esc(battery.entity_id) : "";
    const rangeId = map.range ? esc(map.range.entity_id) : "";
    return `<div class="hero">
      <button class="soc-btn" data-action="more" data-entity="${batteryId}">
        <div class="soc-value">${esc(shown)}<span>%</span></div>
        <div class="bar ${low ? "low" : ""}"><div style="width:${width}%"></div></div>
        <div class="meta">${esc(meta)}</div>
      </button>
      <button class="range-btn" data-action="more" data-entity="${rangeId}">
        <div class="range-value">${esc(range.value)}</div>
        <div class="range-unit">${esc(range.unit || "Range")}</div>
      </button>
    </div>`;
  }

  _controls(map) {
    const tiles = [
      this._lockTile(map.lock),
      this._climateTile(map.ac, map.acMinutes),
      this._actionTile(map.horn, "mdi:bullhorn", "Horn", "press"),
      this._switchTile(map.approach, "mdi:car-parking-lights", "Approach"),
      this._switchTile(map.headlights, "mdi:car-light-dimmed", "Headlights"),
      this._switchTile(map.hazard, "mdi:hazard-lights", "Hazards"),
    ].filter(Boolean);
    if (!tiles.length) return "";
    return `<div class="controls">${tiles.join("")}</div>`;
  }

  _lockTile(state) {
    if (!state) return "";
    const locked = state.state === "locked";
    const unlocked = state.state === "unlocked";
    const label = locked ? "Locked" : unlocked ? "Unlocked" : "Lock";
    const glyph = locked ? "mdi:lock" : "mdi:lock-open-variant";
    const cls = ["tile", unlocked ? "alert" : "", locked ? "on" : "", this._busy.has(state.entity_id) ? "busy" : ""]
      .filter(Boolean)
      .join(" ");
    return `<button class="${cls}" data-action="toggle-lock" data-entity="${esc(state.entity_id)}" aria-label="${esc(label)}">${icon(glyph)}<span>${esc(label)}</span></button>`;
  }

  _switchTile(state, glyph, label) {
    if (!state) return "";
    const on = isOn(state);
    const cls = ["tile", on ? "on" : "", this._busy.has(state.entity_id) ? "busy" : ""].filter(Boolean).join(" ");
    return `<button class="${cls}" data-action="toggle-switch" data-entity="${esc(state.entity_id)}" aria-pressed="${on}" aria-label="${esc(label)}">${icon(glyph)}<span>${esc(label)}</span></button>`;
  }

  _actionTile(state, glyph, label, action) {
    if (!state) return "";
    const cls = ["tile", this._busy.has(state.entity_id) ? "busy" : ""].filter(Boolean).join(" ");
    return `<button class="${cls}" data-action="${action}" data-entity="${esc(state.entity_id)}" aria-label="${esc(label)}">${icon(glyph)}<span>${esc(label)}</span></button>`;
  }

  _climateTile(ac, minutes) {
    if (!ac && !minutes) return "";
    const on = isOn(ac);
    const cls = ["tile", "climate", on ? "on" : "", ac && this._busy.has(ac.entity_id) ? "busy" : ""]
      .filter(Boolean)
      .join(" ");
    const current = minutes && !isBlank(minutes) ? Number(minutes.state) : null;
    const min = Number(minutes?.attributes?.min ?? 0);
    const max = Number(minutes?.attributes?.max ?? 30);
    const duration = current == null || Number.isNaN(current) ? "—" : `${current} min`;
    const acButton = ac
      ? `<button class="tile-hit" data-action="toggle-switch" data-entity="${esc(ac.entity_id)}" aria-pressed="${on}" aria-label="Air conditioning">${icon("mdi:snowflake")}<span>A/C</span><span class="hint">25°</span></button>`
      : "";
    const stepper = minutes
      ? `<div class="stepper">
          <button data-action="duration" data-delta="-1" data-entity="${esc(minutes.entity_id)}" aria-label="Shorter air conditioning" ${current != null && current <= min ? "disabled" : ""}>−</button>
          <span>${esc(duration)}</span>
          <button data-action="duration" data-delta="1" data-entity="${esc(minutes.entity_id)}" aria-label="Longer air conditioning" ${current != null && current >= max ? "disabled" : ""}>+</button>
        </div>`
      : "";
    return `<div class="${cls}">${acButton}${stepper}</div>`;
  }

  _stats(map) {
    const rows = [
      ["aux", "12V battery"],
      ["odometer", "Odometer"],
      ["speed", "Speed"],
      ["serviceDays", "Service due"],
      ["serviceKm", "Service distance"],
    ];
    const buttons = rows
      .filter(([role]) => map[role] && !isBlank(map[role]))
      .map(([role, label]) => {
        const state = map[role];
        return `<button class="stat" data-action="more" data-entity="${esc(state.entity_id)}"><span class="label">${esc(label)}</span><span class="value">${esc(display(state))}</span></button>`;
      })
      .join("");
    if (!buttons) return "";
    return `<section class="section facts"><h3>Car</h3><div class="stats">${buttons}</div></section>`;
  }

  _car(map) {
    const parts = ["tyreFl", "tyreFr", "tyreBl", "tyreBr", "doorFl", "doorFr", "doorRl", "doorRr", "bonnet", "tailgate"];
    if (!parts.some((role) => map[role])) return "";
    const open = (state) => (state && isOn(state) ? "open" : "");
    const zone = (state, label, style) => {
      if (!state) return "";
      return `<button type="button" class="zone" style="${style}" data-action="more" data-entity="${esc(state.entity_id)}" aria-label="${esc(label)}"></button>`;
    };
    const reading = (role, place, label) => {
      const state = map[role];
      const low = isOn(map.tyreLow) ? "low" : "";
      const value = state && !isBlank(state) ? display(state) : "—";
      const action = state ? ` data-action="more" data-entity="${esc(state.entity_id)}"` : "";
      return `<button type="button" class="reading ${place} ${low}"${action} aria-label="${esc(label)} tyre pressure"><span class="where">${esc(label)}</span>${esc(value)}</button>`;
    };
    const lamps = isOn(map.highBeam) ? "high" : isOn(map.headlights) || isOn(map.lowBeam) ? "lit" : "";
    const port = isOn(map.charger) ? "on" : "";
    return `<section class="section car-widget"><h3>Body</h3><div class="car-stage">
      ${reading("tyreFl", "fl", "Front left")}
      ${reading("tyreFr", "fr", "Front right")}
      <div class="car-art">
        <svg class="car-svg" viewBox="0 0 240 460" aria-hidden="true">
          <ellipse class="shadow" cx="120" cy="438" rx="86" ry="12"/>
          <rect class="wheel fl ${isOn(map.tyreLow) ? "low" : ""}" x="16" y="86" width="36" height="64" rx="14"/>
          <circle class="hub" cx="34" cy="118" r="10"/>
          <rect class="wheel fr ${isOn(map.tyreLow) ? "low" : ""}" x="188" y="86" width="36" height="64" rx="14"/>
          <circle class="hub" cx="206" cy="118" r="10"/>
          <rect class="wheel rl ${isOn(map.tyreLow) ? "low" : ""}" x="16" y="292" width="36" height="64" rx="14"/>
          <circle class="hub" cx="34" cy="324" r="10"/>
          <rect class="wheel rr ${isOn(map.tyreLow) ? "low" : ""}" x="188" y="292" width="36" height="64" rx="14"/>
          <circle class="hub" cx="206" cy="324" r="10"/>
          <path class="body" d="M120 22c-42 0-64 28-68 64l-6 78-4 108 4 92c6 48 32 78 74 84 42-6 68-36 74-84l4-92-4-108-6-78c-4-36-26-64-68-64z"/>
          <path class="cladding" d="M58 168c-8 18-12 48-12 86s4 70 12 92c8 6 14 8 18 8V160c-4 0-10 2-18 8zm124 0c8 18 12 48 12 86s-4 70-12 92c-8 6-14 8-18 8V160c4 0 10 2 18 8z"/>
          <path class="panel bonnet ${open(map.bonnet)}" d="M120 40c-28 2-48 20-54 48l2 36h104l2-36c-6-28-26-46-54-48z"/>
          <path class="glass" d="M120 132l-34 28-4 86c14 18 62 18 76 0l-4-86z"/>
          <path class="glass rear" d="M96 268c8 22 40 28 48 10 8 18 40 12 48-10-14 8-34 12-48 12s-34-4-48-12z"/>
          <rect class="panel door fl ${open(map.doorFl)}" x="46" y="156" width="22" height="78" rx="5"/>
          <rect class="panel door fr ${open(map.doorFr)}" x="172" y="156" width="22" height="78" rx="5"/>
          <rect class="panel door rl ${open(map.doorRl)}" x="48" y="242" width="20" height="68" rx="5"/>
          <rect class="panel door rr ${open(map.doorRr)}" x="172" y="242" width="20" height="68" rx="5"/>
          <path class="panel tail ${open(map.tailgate)}" d="M78 352c6 28 20 48 42 54 22-6 36-26 42-54-12 6-28 10-42 10s-30-4-42-10z"/>
          <path class="lamp ${lamps}" d="M62 58c8-8 18-10 26-6-10 8-16 16-16 22-6-4-10-10-10-16z"/>
          <path class="lamp ${lamps}" d="M178 58c-8-8-18-10-26-6 10 8 16 16 16 22 6-4 10-10 10-16z"/>
          <circle class="port ${port}" cx="54" cy="132" r="5"/>
        </svg>
        ${zone(map.bonnet, "Bonnet", "left:22%;top:8%;width:56%;height:16%")}
        ${zone(map.doorFl, "Front left door", "left:14%;top:33%;width:16%;height:16%")}
        ${zone(map.doorFr, "Front right door", "left:70%;top:33%;width:16%;height:16%")}
        ${zone(map.doorRl, "Rear left door", "left:14%;top:51%;width:16%;height:14%")}
        ${zone(map.doorRr, "Rear right door", "left:70%;top:51%;width:16%;height:14%")}
        ${zone(map.tailgate, "Tailgate", "left:24%;top:76%;width:52%;height:14%")}
        ${zone(map.charger, "Charger", "left:16%;top:26%;width:10%;height:8%")}
      </div>
      ${reading("tyreBl", "bl", "Rear left")}
      ${reading("tyreBr", "br", "Rear right")}
    </div></section>`;
  }

  _chips(map) {
    const chips = [];
    const push = (state, onLabel, offLabel, mode) => {
      if (!state) return;
      const on = isOn(state);
      const cls = ["chip", on && mode === "on" ? "on" : "", on && mode === "alert" ? "alert" : ""].filter(Boolean).join(" ");
      chips.push(
        `<button class="${cls}" data-action="more" data-entity="${esc(state.entity_id)}">${esc(on ? onLabel : offLabel)}</button>`
      );
    };
    push(map.ignition, "Ignition on", "Ignition off", "on");
    push(map.highBeam, "High beam on", "High beam off", "on");
    push(map.lowBeam, "Low beam on", "Low beam off", "on");
    push(map.charger, "Charger plugged in", "Charger unplugged", "on");
    push(map.warning, "Warning", "No warning", "alert");
    push(map.tyreLow, "Tyre pressure low", "Tyre pressure ok", "alert");
    push(map.auxLow, "12V battery low", "12V battery ok", "alert");
    if (!chips.length) return "";
    return `<section class="section"><h3>Status</h3><div class="chips">${chips.join("")}</div></section>`;
  }

  _more(entityId) {
    if (!entityId) return;
    this.dispatchEvent(
      new CustomEvent("hass-more-info", {
        detail: { entityId },
        bubbles: true,
        composed: true,
      })
    );
  }

  async _handle(target) {
    const action = target.dataset.action;
    const entityId = target.dataset.entity;
    if (!action || action === "pick") return;
    if (action === "more") {
      this._more(entityId);
      return;
    }
    if (!entityId || this._busy.has(entityId) || target.disabled) return;
    const state = this._hass.states[entityId];
    this._busy.add(entityId);
    this._signatureValue = null;
    this._render();
    try {
      if (action === "toggle-switch") {
        await this._hass.callService("switch", state?.state === "on" ? "turn_off" : "turn_on", {
          entity_id: entityId,
        });
      } else if (action === "toggle-lock") {
        await this._hass.callService("lock", state?.state === "locked" ? "unlock" : "lock", {
          entity_id: entityId,
        });
      } else if (action === "press") {
        await this._hass.callService("button", "press", { entity_id: entityId });
      } else if (action === "duration") {
        const delta = Number(target.dataset.delta);
        const current = Number(state?.state);
        const min = Number(state?.attributes?.min ?? 0);
        const max = Number(state?.attributes?.max ?? 30);
        const step = Number(state?.attributes?.step ?? 1);
        if (!Number.isNaN(current)) {
          const next = Math.min(max, Math.max(min, current + delta * step));
          await this._hass.callService("number", "set_value", { entity_id: entityId, value: next });
        }
      }
    } finally {
      this._busy.delete(entityId);
      this._signatureValue = null;
      if (this._hass) this._render();
    }
  }
}

try {
  if (!customElements.get("tata-ira-card")) {
    customElements.define("tata-ira-card", TataIraCard);
  }
} catch (err) {
  console.error("Tata iRA.ev card", err);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "tata-ira-card")) {
  window.customCards.push({
    type: "tata-ira-card",
    name: "Tata iRA.ev",
    description: "Battery, remote controls, and sensors for a Tata EV",
    preview: true,
  });
}
