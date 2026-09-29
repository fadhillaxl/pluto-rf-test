#!/usr/bin/env python3
"""
Pluto #1 RF receiver/test instrument.

Measures:
  - RSSI estimate from received IQ power
  - noise floor estimate from IQ power
  - SNR estimate = signal power - noise power

For RX1 only:
  python3 rx_test.py --uri ip:192.168.2.10 --rx-channels 1

For RX1 + RX2:
  python3 rx_test.py --uri ip:192.168.2.10 --rx-channels 2

CSV:
  python3 rx_test.py --uri ip:192.168.2.10 --rx-channels 2 --csv results.csv
"""

import argparse
import csv
import time
from datetime import datetime

import numpy as np
import adi


def db10(x):
    return 10.0 * np.log10(max(float(x), 1e-20))


def measure_channel(samples: np.ndarray, sample_rate: float, tone_hz: float,
                    noise_exclusion_hz: float):
    """
    Estimate tone/signal power using an FFT bin neighborhood and noise from
    bins outside the exclusion region.

    This is a relative RF test instrument, not a calibrated dBm power meter.
    """
    x = np.asarray(samples).astype(np.complex64)
    n = len(x)

    # Remove DC offset before FFT.
    x = x - np.mean(x)

    window = np.hanning(n)
    spec = np.fft.fftshift(np.fft.fft(x * window))
    power = np.abs(spec) ** 2
    freqs = np.fft.fftshift(np.fft.fftfreq(n, 1.0 / sample_rate))

    # Look around the configured baseband tone.
    signal_region = np.abs(freqs - tone_hz) <= max(3 * sample_rate / n, 2e3)

    # Exclude DC and signal region from noise estimate.
    noise_region = (
        (np.abs(freqs) > max(3 * sample_rate / n, 2e3))
        & (np.abs(freqs - tone_hz) > noise_exclusion_hz)
    )

    if not np.any(signal_region):
        signal_region[np.argmax(power)] = True
    if not np.any(noise_region):
        noise_region[:] = True
        noise_region[signal_region] = False

    # Integrated spectral power.
    signal_power = np.mean(power[signal_region])
    noise_power = np.mean(power[noise_region])

    signal_db = db10(signal_power)
    noise_db = db10(noise_power)
    snr_db = signal_db - noise_db

    # RMS amplitude in ADC-normalized IQ units.
    rms = np.sqrt(np.mean(np.abs(x) ** 2))
    rms_dbfs = 20 * np.log10(max(float(rms), 1e-12))

    peak_hz = float(freqs[np.argmax(power)])

    return {
        "signal_db": signal_db,
        "noise_db": noise_db,
        "snr_db": snr_db,
        "rms_dbfs": rms_dbfs,
        "peak_hz": peak_hz,
    }


def main():
    p = argparse.ArgumentParser(description="Pluto #1 RF RX measurement tool")
    p.add_argument("--uri", default="ip:192.168.2.10", help="Pluto URI")
    p.add_argument("--freq", type=float, default=434e6, help="RX center frequency in Hz")
    p.add_argument("--bw", type=float, default=1e6, help="RX RF bandwidth in Hz")
    p.add_argument("--sample-rate", type=float, default=2e6, help="RX sample rate in Hz")
    p.add_argument("--rx-gain", type=float, default=30, help="RX manual gain in dB")
    p.add_argument("--rx-channels", type=int, choices=[1, 2], default=1, help="1=RX1, 2=RX1+RX2")
    p.add_argument("--tone", type=float, default=100e3, help="Expected baseband tone offset in Hz")
    p.add_argument("--buffer", type=int, default=16384, help="RX buffer size")
    p.add_argument("--interval", type=float, default=1.0, help="Seconds between measurements")
    p.add_argument("--duration", type=float, default=0, help="Seconds; 0 = until Ctrl+C")
    p.add_argument("--csv", default="", help="Optional CSV output path")
    args = p.parse_args()

    if abs(args.tone) >= args.sample_rate / 2:
        raise SystemExit("--tone must be below sample-rate/2")

    print(f"Connecting to Pluto RX: {args.uri}")
    sdr = adi.Pluto(args.uri)

    sdr.rx_enabled_channels = [0] if args.rx_channels == 1 else [0, 1]
    sdr.rx_lo = int(args.freq)
    sdr.rx_rf_bandwidth = int(args.bw)
    sdr.rx_sample_rate = int(args.sample_rate)
    sdr.gain_control_mode_chan0 = "manual"
    sdr.rx_hardwaregain_chan0 = args.rx_gain
    if args.rx_channels == 2:
        sdr.gain_control_mode_chan1 = "manual"
        sdr.rx_hardwaregain_chan1 = args.rx_gain
    sdr.rx_buffer_size = args.buffer

    csv_file = None
    writer = None
    if args.csv:
        csv_file = open(args.csv, "w", newline="")
        fields = [
            "timestamp", "elapsed_s", "channel", "frequency_hz",
            "bandwidth_hz", "sample_rate_hz", "rx_gain_db",
            "signal_db", "noise_db", "snr_db", "rms_dbfs", "peak_hz"
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()

    print("\n=== Pluto RX TEST ===")
    print(f"URI          : {args.uri}")
    print(f"Frequency    : {args.freq/1e6:.6f} MHz")
    print(f"Bandwidth    : {args.bw/1e6:.3f} MHz")
    print(f"Sample rate  : {args.sample_rate/1e6:.3f} MSPS")
    print(f"RX gain      : {args.rx_gain:.1f} dB")
    print(f"RX channels  : {'RX1 + RX2' if args.rx_channels == 2 else 'RX1'}")
    print(f"Tone         : {args.tone/1e3:.1f} kHz")
    print("\nWARNING: signal_db/noise_db are relative FFT power values, not calibrated dBm.")
    print("Use the same settings for every test so the comparisons are meaningful.")
    print("\nPress Ctrl+C to stop.\n")

    start = time.monotonic()
    try:
        while True:
            raw = sdr.rx()
            samples = raw if args.rx_channels == 2 else [raw]

            now = datetime.now().astimezone().isoformat(timespec="seconds")
            elapsed = time.monotonic() - start

            print(f"[{now}]")
            for idx, ch in enumerate(samples, start=1):
                m = measure_channel(
                    ch,
                    args.sample_rate,
                    args.tone,
                    noise_exclusion_hz=max(10e3, 4 * args.sample_rate / args.buffer),
                )
                print(
                    f"  RX{idx}: "
                    f"signal={m['signal_db']:8.2f} dB  "
                    f"noise={m['noise_db']:8.2f} dB  "
                    f"SNR={m['snr_db']:7.2f} dB  "
                    f"RMS={m['rms_dbfs']:7.2f} dBFS  "
                    f"peak={m['peak_hz']/1e3:8.2f} kHz"
                )

                if writer:
                    writer.writerow({
                        "timestamp": now,
                        "elapsed_s": f"{elapsed:.3f}",
                        "channel": idx,
                        "frequency_hz": int(args.freq),
                        "bandwidth_hz": int(args.bw),
                        "sample_rate_hz": int(args.sample_rate),
                        "rx_gain_db": args.rx_gain,
                        **{k: f"{v:.6f}" for k, v in m.items()},
                    })
                    csv_file.flush()

            time.sleep(args.interval)

            if args.duration > 0 and elapsed >= args.duration:
                break

    except KeyboardInterrupt:
        print("\nStopping RX test...")
    finally:
        if csv_file:
            csv_file.close()


if __name__ == "__main__":
    main()
