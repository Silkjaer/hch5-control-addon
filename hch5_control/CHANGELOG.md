# Changelog

## 1.6.1-silkjaer.5

- Works for every HCH5: `unit` (mk1/mk2) and `connection` (tcp/serial) replace
  the adapter-only setup, including USB-RS485 adapters and MKII over Modbus TCP
  or RTU. The controller talks to the unit directly, as it does on a Raspberry Pi.
- `read_only` (MK1 behind a TCP adapter) replaces the `bus_access` levels.
  **Breaking:** set the new options after updating.

## 1.6.1-silkjaer.4

- New bus access level `fans_bypass_fireplace`: also allows register 76, which
  fireplace and standby mode need. On a unit without HAC1 that is everything
  the controller writes.

## 1.6.1-silkjaer.3

- The WebUI opens inside Home Assistant (ingress) and has its own sidebar entry,
  "Ventilation". Home Assistant's login is used: no separate WebUI login there.
  Port 8088 stays for the integration's controller API and needs the WebUI login.

## 1.6.1-silkjaer.2

- Import an existing installation from `share/hch5_control_import` at start,
  for setups where the `addon_configs` folder is not visible.
- Run in Home Assistant's time zone. The controller ran in UTC, so the week
  plan and night mode were an hour off.

## 1.6.1-silkjaer.1

- First app build: HCH5 Control 1.6.1 from Silkjaer/dantherm-control `integration`
  (TCP adapter support, HAC1 detection, WebUI without afterheat when HAC1 is
  missing, login fixes) with a bus guard in front of the adapter.
