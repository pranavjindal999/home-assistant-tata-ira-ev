// Tata iRA.ev dashboard card. One card for every control and sensor on the car.

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
  battery_temperature: "batteryTemp",
  interior_temperature: "interior",
  battery_energy: "energy",
  aux_battery: "aux",
  telematics_battery: "telematics",
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
  key: "key",
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
  battery_temperature: "batteryTemp",
  interior_temperature: "interior",
  battery_energy: "energy",
  "12v_battery": "aux",
  telematics_battery: "telematics",
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
  key_in_car: "key",
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
ha-card { display: block; }
.wrap {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  color: var(--primary-text-color);
}
header { display: flex; align-items: flex-start; gap: 12px; }
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
}
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
.tyres {
  display: grid;
  grid-template-columns: 1fr 36px 1fr;
  grid-template-areas: "fl spine fr" "bl spine br";
  gap: 8px;
  align-items: stretch;
}
.spine {
  grid-area: spine;
  border-radius: 14px;
  background: color-mix(in srgb, var(--primary-text-color) 8%, transparent);
}
.tyre { border: 0; background: transparent; border-radius: 12px; border: 1px solid var(--divider-color); padding: 8px 10px; text-align: left; }
.tyre.fl { grid-area: fl; }
.tyre.fr { grid-area: fr; text-align: right; }
.tyre.bl { grid-area: bl; }
.tyre.br { grid-area: br; text-align: right; }
.tyre .label { font-size: 11px; color: var(--secondary-text-color); }
.tyre .value { font-size: 16px; font-weight: 500; margin-top: 2px; }
.tyre.alert { border-color: var(--error-color, #c62828); color: var(--error-color, #c62828); }
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
.location {
  width: 100%;
  border-radius: 12px;
  border: 1px solid var(--divider-color);
  background: transparent;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
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
button:focus-visible, .stat:focus-visible, .chip:focus-visible, .tyre:focus-visible {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}
@media (hover: hover) {
  .tile:hover, .stat:hover, .chip:hover, .tyre:hover, .location:hover, .icon-btn:hover {
    background: color-mix(in srgb, var(--primary-text-color) 6%, transparent);
  }
  .tile.on:hover { background: color-mix(in srgb, var(--primary-color) 22%, transparent); }
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
  if (!vehicleId || !uniqueId) return null;
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

function devicesFrom(hass, cached) {
  const source = hass.devices ? Object.values(hass.devices) : cached || [];
  return source.filter(
    (device) =>
      (device.identifiers || []).some((id) => id[0] === "tata_ira") ||
      (device.manufacturer === "Tata Motors" && device.model === "iRA.ev")
  );
}

function entriesFrom(hass, registry) {
  if (registry) return registry;
  if (!hass.entities) return [];
  return Object.values(hass.entities);
}

function indexCar(device, entries, states) {
  const ident = (device.identifiers || []).find((id) => id[0] === "tata_ira");
  const vehicleId = ident ? ident[1] : null;
  const ranked = [];
  for (const entry of entries) {
    if (entry.device_id !== device.id) continue;
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
    if (!config || Array.isArray(config)) {
      throw new Error("Invalid card configuration");
    }
    this._config = config;
    if (this._hass) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    const signature = this._signature();
    if (signature === this._signatureValue) return;
    this._signatureValue = signature;
    this._render();
    if (!this._registryRequested) {
      this._registryRequested = true;
      this._loadRegistry();
    }
  }

  getCardSize() {
    return 10;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6, rows: "auto" };
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
    if (!this.shadowRoot.querySelector("#body")) {
      this.shadowRoot.innerHTML = `<style>${STYLE}</style><div id="body"></div>`;
      this.shadowRoot.getElementById("body").addEventListener("click", (event) => {
        const target = event.target.closest("[data-action]");
        if (!target || !this.shadowRoot.contains(target) || target.dataset.action === "pick") return;
        event.preventDefault();
        event.stopPropagation();
        this._handle(target);
      });
      this.shadowRoot.getElementById("body").addEventListener("change", (event) => {
        const select = event.target.closest("[data-action='pick']");
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
    parts.push(this._controls(map));
    parts.push(this._stats(map));
    parts.push(this._tyres(map));
    parts.push(this._chips(map));
    if (map.location) {
      parts.push(
        `<button class="location" data-action="more" data-entity="${esc(map.location.entity_id)}">${icon("mdi:map-marker")}<span>Location</span></button>`
      );
    }
    return parts.filter(Boolean).join("");
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
      <div><div class="name">${esc(name)}</div><div class="sub">${esc(bits.join(" · ") || "Tata iRA.ev")}</div></div>
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
      ["interior", "Interior"],
      ["batteryTemp", "Battery temp"],
      ["energy", "Energy"],
      ["aux", "12V battery"],
      ["telematics", "Telematics"],
      ["odometer", "Odometer"],
      ["speed", "Speed"],
      ["serviceDays", "Service due"],
      ["serviceKm", "Service distance"],
    ];
    const buttons = rows
      .filter(([role]) => map[role])
      .map(([role, label]) => {
        const state = map[role];
        return `<button class="stat" data-action="more" data-entity="${esc(state.entity_id)}"><span class="label">${esc(label)}</span><span class="value">${esc(display(state))}</span></button>`;
      })
      .join("");
    if (!buttons) return "";
    return `<section class="section"><h3>Car</h3><div class="stats">${buttons}</div></section>`;
  }

  _tyres(map) {
    const cells = [
      ["tyreFl", "Front left", "fl"],
      ["tyreFr", "Front right", "fr"],
      ["tyreBl", "Back left", "bl"],
      ["tyreBr", "Back right", "br"],
    ];
    if (!cells.some(([role]) => map[role])) return "";
    const low = isOn(map.tyreLow);
    const buttons = cells
      .map(([role, label, place]) => {
        const state = map[role];
        if (!state) return `<div class="tyre ${place}"><div class="label">${esc(label)}</div><div class="value">—</div></div>`;
        return `<button class="tyre ${place} ${low ? "alert" : ""}" data-action="more" data-entity="${esc(state.entity_id)}" aria-label="${esc(label)}"><div class="label">${esc(label)}</div><div class="value">${esc(display(state))}</div></button>`;
      })
      .join("");
    return `<section class="section"><h3>Tyres</h3><div class="tyres">${buttons}<div class="spine"></div></div></section>`;
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
    const openings = [
      [map.doorFl, "Front left open"],
      [map.doorFr, "Front right open"],
      [map.doorRl, "Rear left open"],
      [map.doorRr, "Rear right open"],
      [map.bonnet, "Bonnet open"],
      [map.tailgate, "Tailgate open"],
    ].filter(([state]) => state);
    const openOnes = openings.filter(([state]) => isOn(state));
    if (openings.length && !openOnes.length) {
      chips.push(`<span class="chip">Openings shut</span>`);
    } else {
      for (const [state, label] of openOnes) {
        chips.push(
          `<button class="chip alert" data-action="more" data-entity="${esc(state.entity_id)}">${esc(label)}</button>`
        );
      }
    }
    push(map.ignition, "Ignition on", "Ignition off", "on");
    push(map.key, "Key in car", "Key not in car", "on");
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

if (!customElements.get("tata-ira-card")) {
  customElements.define("tata-ira-card", TataIraCard);
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
