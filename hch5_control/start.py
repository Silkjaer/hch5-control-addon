#!/usr/bin/env python3
"""Run HCH5 Control as a Home Assistant app.

* Options come from /data/options.json (the app's Configuration tab).
* All controller state lives in the app's config folder: /config here,
  addon_configs/<slug>/state over Samba, and part of Home Assistant backups.
* Files placed in share/hch5_control_import (visible in every Samba or SSH
  setup) are moved into that state folder at the next start, to bring over an
  existing installation.
* Unless bus_access is "direct", the bus guard sits between the controller
  and the RS485 adapter and forwards only what bus_access allows.
* The guard and the controller are restarted on their own if they stop, like
  systemd's Restart=always on a Raspberry Pi install.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import yaml

OPTIONS = Path("/data/options.json")
STATE_DIR = Path("/config/state")
STATE_LINK = Path("/var/lib/dantherm-hch5-ha")
IMPORT_DIR = Path("/share/hch5_control_import")
CONTROLLER_CONFIG = Path("/data/controller.yaml")
APP_DIR = Path("/opt/dantherm-passivelink-webui")
GUARD = Path("/opt/bus_guard.py")
GUARD_LISTEN = ("127.0.0.1", 4300)
# Home Assistant's ingress proxy; its requests are logged in as the WebUI admin.
INGRESS_PROXY = "172.30.32.2"

# What each bus_access level lets through the guard (see bus_guard.py).
GUARD_ALLOW = {
    "read_only": "",
    "read": "read",
    "fans": "read,write:1:66/67",
    "fans_bypass": "read,write:1:66/67/68",
}


def log(message: str) -> None:
    print(f"[hch5-control] {message}", flush=True)


def link_state_dir() -> None:
    """Point the controller's fixed state path at the app's config folder."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if STATE_LINK.is_symlink():
        STATE_LINK.unlink()
    elif STATE_LINK.exists():
        raise SystemExit(f"{STATE_LINK} exists and is not a link")
    STATE_LINK.parent.mkdir(parents=True, exist_ok=True)
    STATE_LINK.symlink_to(STATE_DIR)


def import_state() -> None:
    """Move an earlier installation's files from the share folder into state.

    The folder is renamed afterwards, so the import runs once and the copy
    stays as a backup until it is deleted by hand.
    """
    if not IMPORT_DIR.is_dir():
        return
    files = [path for path in IMPORT_DIR.iterdir() if path.is_file() and not path.name.startswith(".")]
    if not files:
        return
    for path in files:
        shutil.copy2(path, STATE_DIR / path.name)
    done = IMPORT_DIR.with_name(f"{IMPORT_DIR.name}.done-{time.strftime('%Y%m%d-%H%M%S')}")
    IMPORT_DIR.rename(done)
    log(f"imported {len(files)} file(s) from {IMPORT_DIR}: {', '.join(sorted(p.name for p in files))}; folder renamed to {done.name}")


def controller_config(serial_port: str) -> dict:
    """The installer's defaults (install.sh), with the given serial port."""
    return {
        "device": {"id": "dantherm_hch5", "name": "Dantherm HCH5"},
        "mqtt": {"enabled": False, "topic_prefix": "dantherm",
                 "discovery_prefix": "homeassistant", "retain": True},
        "serial": {"port": serial_port, "baudrate": 19200, "parity": "E",
                   "active_reads_enabled": True, "master_mode": True},
        "raw_tcp": {"enabled": True, "bind": "0.0.0.0", "port": 4196, "max_clients": 4},
        "dashboard": {"enabled": True, "bind": "0.0.0.0", "port": 8080,
                      "preheater_url": "http://127.0.0.1:4197/temperatures"},
        "controller": {
            "state_file": str(STATE_LINK / "controller.json"),
            "tick_seconds": 2.0,
            "master_arbitration": {
                "detection_window_seconds": 2,
                "detection_min_foreign_writes": 2,
                "release_timeout_seconds": 10,
                "startup_observation_seconds": 10,
                "own_echo_ttl_seconds": 0.2,
            },
        },
        "control": {"enabled": False, "fireplace_enabled": False},
        "diagnostic_capture": {"directory": str(STATE_LINK / "direction-captures")},
        "filter": {"enabled": False},
    }


def wait_for_port(address: tuple[str, int], seconds: float) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(address, timeout=1):
                return True
        except OSError:
            time.sleep(0.2)
    return False


class Service:
    """A child process that is started again after it stops."""

    def __init__(self, name: str, args: list[str], env: dict[str, str]):
        self.name, self.args, self.env = name, args, env
        self.process: subprocess.Popen | None = None
        self.started = 0.0

    def start(self) -> None:
        log(f"starting {self.name}")
        self.process = subprocess.Popen(self.args, env=self.env, cwd=APP_DIR)
        self.started = time.monotonic()

    def check(self) -> None:
        if self.process is None or self.process.poll() is None:
            return
        code = self.process.returncode
        # Back off when it dies straight away, so a bad setting does not spin.
        delay = 3.0 if time.monotonic() - self.started > 30 else 15.0
        log(f"{self.name} stopped with code {code}; restarting in {delay:.0f} s")
        time.sleep(delay)
        self.start()

    def stop(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()


def main() -> int:
    options = json.loads(OPTIONS.read_text())
    adapter = f"{options['adapter_host']}:{options['adapter_port']}"
    access = options.get("bus_access", "read_only")
    link_state_dir()
    import_state()

    env = dict(os.environ)
    env["PYTHONUNBUFFERED"] = "1"
    env["DANTHERM_WEBUI_AUTH_FILE"] = str(STATE_LINK / "webui-auth.json")
    env["DANTHERM_INGRESS_PROXY"] = INGRESS_PROXY
    if options.get("controller_token"):
        env["DANTHERM_CONTROLLER_TOKEN"] = options["controller_token"]

    services: list[Service] = []
    if access == "direct":
        log(f"bus access: direct to {adapter} (no guard)")
        serial_port = f"socket://{adapter}"
    else:
        allow = GUARD_ALLOW[access]
        log(f"bus access: {access} through the guard to {adapter} (allow: {allow or 'nothing'})")
        guard = Service("bus guard", [sys.executable, "-u", str(GUARD)], {
            **env,
            "UPSTREAM": adapter,
            "LISTEN": f"{GUARD_LISTEN[0]}:{GUARD_LISTEN[1]}",
            "ALLOW": allow,
            "TX_LOG": str(STATE_DIR / "bus-guard.log"),
            "TX_LOG_READS": "0",
        })
        guard.start()
        services.append(guard)
        if not wait_for_port(GUARD_LISTEN, 15):
            log("bus guard did not start listening; continuing, the controller will retry")
        serial_port = f"socket://{GUARD_LISTEN[0]}:{GUARD_LISTEN[1]}"

    CONTROLLER_CONFIG.write_text(yaml.safe_dump(controller_config(serial_port), sort_keys=False))
    controller = Service("controller", [
        sys.executable, "-u", "dantherm_controller_gateway.py",
        "-c", str(CONTROLLER_CONFIG),
        "--log-level", str(options.get("log_level") or "info").upper(),
    ], env)
    controller.start()
    services.append(controller)

    running = True

    def shutdown(*_args) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    while running:
        for service in services:
            service.check()
        time.sleep(1)
    log("stopping")
    for service in reversed(services):
        service.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
