#!/usr/bin/env python3
"""
Pluto #2 transmitter for RF/RSSI/SNR testing.

Example:
  python3 tx.py --uri ip:192.168.2.11 --freq 434e6 --bw 1e6 --sample-rate 2e6
"""

import argparse
import time
import numpy as np
import adi
from rf_config import load_config, normalize_uri


def tone_iq(sample_rate: float, tone_hz: float, n: int) -> np.ndarray:
    t = np.arange(n, dtype=np.float64) / sample_rate
    x = np.exp(2j * np.pi * tone_hz * t)
    return x.astype(np.complex64)


def main():
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--config", default="", help="Custom config file")
    pre_args, _ = pre_parser.parse_known_args()

    cfg, cfg_file = load_config(pre_args.config)

    p = argparse.ArgumentParser(description="Pluto #2 RF test transmitter")
    p.add_argument("--config", default=pre_args.config, help="Path to config file (.config, .comfig, config.ini)")
    p.add_argument("--uri", default=cfg["uri"], help=f"Pluto URI (default: {cfg['uri']})")
    p.add_argument("--freq", type=float, default=cfg["freq"], help="TX center frequency in Hz")
    p.add_argument("--bw", type=float, default=cfg["bw"], help="TX RF bandwidth in Hz")
    p.add_argument("--sample-rate", type=float, default=cfg["sample_rate"], help="TX sample rate in Hz")
    p.add_argument("--tx-gain", type=float, default=cfg["tx_gain"], help="TX hardware gain in dB; Pluto commonly uses negative dB")
    p.add_argument("--tone", type=float, default=cfg["tone"], help="Baseband tone offset in Hz")
    p.add_argument("--buffer", type=int, default=cfg["buffer"], help="TX buffer size")
    p.add_argument("--duration", type=float, default=cfg["duration"], help="Seconds to transmit; 0 = continuous")
    args = p.parse_args()

    args.uri = normalize_uri(args.uri)
    if cfg_file:
        print(f"[Config] Loaded settings from: {cfg_file}")

    if abs(args.tone) >= args.sample_rate / 2:
        raise SystemExit("--tone must be below sample-rate/2")

    print(f"Connecting to Pluto TX: {args.uri}")
    sdr = adi.Pluto(args.uri)

    sdr.tx_enabled_channels = [0]
    sdr.tx_lo = int(args.freq)
    sdr.tx_rf_bandwidth = int(args.bw)
    sdr.tx_sample_rate = int(args.sample_rate)
    sdr.tx_hardwaregain_chan0 = args.tx_gain
    sdr.tx_cyclic_buffer = True
    sdr.tx_buffer_size = args.buffer

    # Tone amplitude 0.25 leaves substantial digital headroom.
    data = 0.25 * tone_iq(args.sample_rate, args.tone, args.buffer)

    print("\n=== Pluto TX ===")
    print(f"URI          : {args.uri}")
    print(f"Frequency    : {args.freq/1e6:.6f} MHz")
    print(f"Bandwidth    : {args.bw/1e6:.3f} MHz")
    print(f"Sample rate  : {args.sample_rate/1e6:.3f} MSPS")
    print(f"TX gain      : {args.tx_gain:.1f} dB")
    print(f"Tone         : {args.tone/1e3:.1f} kHz")
    print("Transmitting... Ctrl+C to stop.")

    sdr.tx(data)

    start = time.monotonic()
    try:
        while True:
            if args.duration > 0 and time.monotonic() - start >= args.duration:
                break
            time.sleep(0.25)
    except KeyboardInterrupt:
        print("\nStopping TX...")
    finally:
        try:
            sdr.tx_destroy_buffer()
        except Exception:
            pass


if __name__ == "__main__":
    main()
