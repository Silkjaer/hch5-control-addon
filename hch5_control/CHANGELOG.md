# Changelog

## 1.6.1-silkjaer.7

Fixes from a code audit:

- Temperatures below zero are read as negative. At −5 °C the controller
  showed 650 °C.
- A command that keeps failing is retried every minute instead of being given
  up after three tries. A write whose reply was lost no longer hides a later
  correction. The bypass request is checked against the unit every minute.
- Readings that stop arriving expire after two minutes instead of steering
  free cooling.
- Free cooling stops as soon as the outdoor air is below its lowest outdoor
  temperature; the minimum run time no longer keeps the bypass open there.
- New alarm when the bypass damper has not reached the requested position
  within 5 minutes (stuck damper or motor).
- Nothing is written to HAC1 until it has answered.
- The ingress login cookie is limited to this app's ingress path, so other
  apps on the host no longer receive it.
- The watchdog uses the new `/healthz`, which fails when the bus loop or the
  controller has stopped, not only when the web server is down.
- RS485 frames that arrive in pieces through the adapter are no longer lost,
  a HAC1 acknowledgement needs a valid CRC (an echo of our own write no longer
  counts), and the Pi listens a full 10 s for an HCP4 after the port opens.
- Python packages are pinned.

## 1.6.1-silkjaer.6

- Without HAC1 the log no longer shows "Controller write failed: HAC1 not
  installed" every 15 minutes or an afterheat refresh error at start-up: the
  controller skips the afterheat setpoint once HAC1 is known to be missing.

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
