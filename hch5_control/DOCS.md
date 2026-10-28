# HCH5 Control

Local control of a Dantherm HCH5, with its WebUI inside Home Assistant. The app
runs the controller from
[Silkjaer/dantherm-control](https://github.com/Silkjaer/dantherm-control),
which builds on [MRDonnii/dantherm-control](https://github.com/MRDonnii/dantherm-control).

| Unit | Connection |
|---|---|
| **HCH5 MK1** (with or without HAC1) | The RS485 bus, through an RS485-to-Ethernet adapter in transparent TCP mode (for example Waveshare, 19200 8E1) or a USB-RS485 adapter in the Home Assistant machine |
| **HCH5 MKII** | The unit's own Modbus, over TCP (port 502) or RTU through USB |

> Unofficial community project. Not developed, approved or supported by
> Dantherm. Changing how the unit is controlled is at your own risk. Keep the
> HCP4 panel (MK1) so the installation can be returned to its original setup.

## How it works

The WebUI opens inside Home Assistant through *Open web UI* or **Ventilation**
in the sidebar. You are signed in as the WebUI's administrator, because Home
Assistant has already signed you in; the panel is shown to Home Assistant
administrators only. Port 8088 serves the Home Assistant integration's
controller API; there the WebUI still asks for its own login.

The controller keeps its own safety: on an MK1 it takes over the bus only after
HCP4 has been quiet for 10 seconds and steps back as soon as HCP4 writes again.
It finds out by itself whether a HAC1 is installed and hides the afterheat
parts when it is not, and it sends only verified commands. To control an MK1,
disconnect HCP4 from the RS485 line.

## Options

| Option | Meaning |
|---|---|
| `unit` | `mk1` or `mk2` |
| `connection` | `tcp` (network) or `serial` (USB adapter in the Home Assistant machine) |
| `adapter_host`, `adapter_port` | With `tcp`: the RS485 adapter's IP and port (MK1, often 4196) or the unit's IP (MKII, port 502). An empty port uses the default |
| `serial_device` | With `serial`: the USB-RS485 adapter |
| `mk2_unit_id` | The MKII's Modbus address, default 1 |
| `read_only` | Read only, to try the app next to other control. See below |
| `controller_token` | Optional fixed key for the Home Assistant integration. Empty: create one in the WebUI |
| `log_level` | Log level, default `info` |

**`read_only`** exists only for an MK1 behind a TCP adapter. A small bus guard
then sits between the controller and the adapter and forwards nothing;
everything it refuses is logged in `state/bus-guard.log`. The controller shows
data and its decisions but does not control the unit. With USB or an MKII the
app refuses `read_only`.

## Only one controller at a time

An RS485-to-Ethernet adapter does not pass what it sends on the bus to its
other TCP clients. Two controllers behind the same adapter therefore **cannot
see each other**, and both will believe they are the bus master. Always stop
any other controller before this app takes control, or run it with `read_only`.

## Data and backups

All state lives in the app's config folder, `addon_configs/<id>_hch5_control/state`,
and is part of Home Assistant backups: settings, rooms and commissioning,
users, history and logs.

**Moving from another installation:** put the files from the old
`/var/lib/dantherm-hch5-ha` (or `docker/data`) into `share/hch5_control_import`
and start or restart the app. It moves them into `state` and renames the import
folder to `hch5_control_import.done-<time>`, so the import runs once. You can
also copy straight into `state` if you can see `addon_configs` (the Terminal &
SSH app cannot).

## The Home Assistant integration

Use [dantherm-control-ha](https://github.com/Silkjaer/dantherm-control-ha):

- **Data (MK1):** set a host port for `4196/tcp` in the app's network settings
  and point the integration's "RS485 over TCP" at that port on the Home
  Assistant host (`127.0.0.1` works). The mirror repeats the controller's reads
  with both request and answer, which the integration cannot see straight from
  the adapter once the controller is the bus master. It also leaves the adapter
  with a single client.
- **Data (MKII):** set a host port for `5020/tcp` and add the integration as
  "HCH5 MKII – Modbus TCP" on that port.
- **Control:** turn on "Connect to the controller API" with `127.0.0.1`, port
  8088 and the key from the WebUI (*Home Assistant → Connection from Home
  Assistant*) or `controller_token`.

## Back to HCP4 (MK1)

Stop the app (or turn on `read_only`) and reconnect HCP4. The unit keeps the
last fan and bypass values until HCP4 writes.
