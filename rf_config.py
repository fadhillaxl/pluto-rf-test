"""
rf_config.py
Helper for loading SDR and RF test configurations from .config, .comfig, or config.ini.
"""

import configparser
import os
import re
import sys
from pathlib import Path


def auto_patch_iio():
    """
    Auto-patches iio.py in the current environment if running on an OS with an older
    system libiio (such as Ubuntu 20.04 / Focal) where 'iio_device_get_label' symbol
    does not exist in /usr/lib/.../libiio.so.0.
    """
    for p in sys.path:
        candidate = Path(p) / "iio.py"
        if candidate.is_file():
            try:
                content = candidate.read_text(encoding="utf-8")
                target = (
                    "_d_get_label = _lib.iio_device_get_label\n"
                    "_d_get_label.restype = c_char_p\n"
                    "_d_get_label.argtypes = (_DevicePtr,)"
                )
                replacement = (
                    "try:\n"
                    "    _d_get_label = _lib.iio_device_get_label\n"
                    "    _d_get_label.restype = c_char_p\n"
                    "    _d_get_label.argtypes = (_DevicePtr,)\n"
                    "except AttributeError:\n"
                    "    _d_get_label = lambda dev: None"
                )
                if target in content:
                    candidate.write_text(content.replace(target, replacement), encoding="utf-8")
                    print(f"[Compat] Applied compatibility fix to {candidate} (libiio older symbol patch)")
            except Exception:
                pass
            break


# Run auto-patch before any other code imports adi/iio
auto_patch_iio()



def normalize_uri(uri: str) -> str:
    """Normalize URI to a valid libiio format."""
    uri = uri.strip()
    if not uri:
        return "usb:"
    # If user provided macOS /dev/tty.usbmodem... or usb:/dev/tty...
    # Pluto via USB uses libiio 'usb:' or USB-Ethernet 'ip:192.168.2.10'
    if "/dev/tty" in uri or "usbmodem" in uri:
        return "ip:192.168.2.10"
    # If raw IP without 'ip:' prefix (e.g., 192.168.99.240 or 192.168.99.240:1234)
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?$", uri):
        return f"ip:{uri}"
    if uri.lower() == "usb":
        return "usb:"
    return uri


def find_config_file(custom_path: str = None) -> str:
    """Find configuration file from custom path or standard names."""
    if custom_path and os.path.exists(custom_path):
        return str(Path(custom_path).resolve())

    # Supported config file names (including user typo .comfig)
    candidates = [".config", ".comfig", "config.ini"]
    search_dirs = [Path.cwd(), Path(__file__).resolve().parent]

    for d in search_dirs:
        for name in candidates:
            p = d / name
            if p.is_file():
                return str(p.resolve())

    return ""


def load_config(custom_path: str = None) -> tuple[dict, str]:
    """
    Load configuration from file.
    Returns (dict_of_defaults, config_file_path_or_empty).
    """
    defaults = {
        "uri": "usb:",
        "freq": 434e6,
        "bw": 1e6,
        "sample_rate": 2e6,
        "tone": 100e3,
        "buffer": 16384,
        "tx_gain": -20.0,
        "duration": 0.0,
        "rx_gain": 30.0,
        "rx_channels": 1,
        "interval": 1.0,
        "csv": "",
    }

    config_path = find_config_file(custom_path)
    if not config_path:
        return defaults, ""

    cfg = configparser.ConfigParser(interpolation=None)
    try:
        cfg.read(config_path)
    except Exception as e:
        print(f"[Config Warning] Gagal membaca {config_path}: {e}")
        return defaults, ""

    # Check for device target profile (e.g. target = laptop or target = sbc)
    target = None
    if cfg.has_section("device") and cfg.has_option("device", "target"):
        target = cfg.get("device", "target").strip().lower()

    if target and cfg.has_section(target) and cfg.has_option(target, "uri"):
        defaults["uri"] = normalize_uri(cfg.get(target, "uri"))
    elif cfg.has_section("sdr") and cfg.has_option("sdr", "uri"):
        defaults["uri"] = normalize_uri(cfg.get("sdr", "uri"))

    # [rf] section
    if cfg.has_section("rf"):
        for key in ["freq", "bw", "sample_rate", "tone"]:
            if cfg.has_option("rf", key):
                try:
                    defaults[key] = float(cfg.get("rf", key))
                except ValueError:
                    pass
        if cfg.has_option("rf", "buffer"):
            try:
                defaults["buffer"] = int(cfg.get("rf", "buffer"))
            except ValueError:
                pass

    # [tx] section
    if cfg.has_section("tx"):
        if cfg.has_option("tx", "tx_gain"):
            try:
                defaults["tx_gain"] = float(cfg.get("tx", "tx_gain"))
            except ValueError:
                pass
        if cfg.has_option("tx", "duration"):
            try:
                defaults["duration"] = float(cfg.get("tx", "duration"))
            except ValueError:
                pass

    # [rx] section
    if cfg.has_section("rx"):
        if cfg.has_option("rx", "rx_gain"):
            try:
                defaults["rx_gain"] = float(cfg.get("rx", "rx_gain"))
            except ValueError:
                pass
        if cfg.has_option("rx", "rx_channels"):
            try:
                defaults["rx_channels"] = int(cfg.get("rx", "rx_channels"))
            except ValueError:
                pass
        if cfg.has_option("rx", "interval"):
            try:
                defaults["interval"] = float(cfg.get("rx", "interval"))
            except ValueError:
                pass
        if cfg.has_option("rx", "duration"):
            try:
                defaults["duration"] = float(cfg.get("rx", "duration"))
            except ValueError:
                pass
        if cfg.has_option("rx", "csv"):
            defaults["csv"] = cfg.get("rx", "csv").strip()

    return defaults, config_path
