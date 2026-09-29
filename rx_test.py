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
from rf_config import load_config, normalize_uri
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


def combine_mrc(ch1: np.ndarray, ch2: np.ndarray, sample_rate: float, tone_hz: float):
    """
    Maximal Ratio Combining (MRC) untuk menggabungkan 2 kanal antena penerima (RX1 + RX2)
    menjadi 1 sinyal digital dengan SNR optimal (Diversity Combining: 2 RX jadi 1).
    Tahan terhadap Carrier Frequency Offset (CFO) antara TX dan RX SDR.
    """
    x1 = np.asarray(ch1).astype(np.complex64)
    x2 = np.asarray(ch2).astype(np.complex64)
    n = min(len(x1), len(x2))
    x1 = x1[:n] - np.mean(x1[:n])
    x2 = x2[:n] - np.mean(x2[:n])

    # Gunakan FFT untuk mendeteksi frekuensi dan fasa tone aktual (tahan CFO)
    win = np.hanning(n)
    X1 = np.fft.fft(x1 * win)
    X2 = np.fft.fft(x2 * win)
    freqs = np.fft.fftfreq(n, 1.0 / sample_rate)

    # Cari peak di sekitar expected tone (+- 20 kHz toleransi CFO)
    region = np.abs(freqs - tone_hz) <= max(20e3, 5 * sample_rate / n)
    if not np.any(region):
        region[:] = True

    power1 = np.abs(X1) ** 2
    idx_peak = np.where(region)[0][np.argmax(power1[region])]

    # Amplitudo & fasa kompleks di peak
    c1 = X1[idx_peak]
    c2 = X2[idx_peak]

    # Beda fasa antara RX2 dan RX1: delta_phi = angle(c2) - angle(c1)
    phase_diff = np.angle(c2) - np.angle(c1)

    # Putar fasa kanal 2 agar sefasa sempurna (koheren) dengan kanal 1
    x2_aligned = x2 * np.exp(-1j * phase_diff)

    # Estimasi variansi noise dari kedua kanal
    noise_mask = (np.abs(freqs) > 2e3) & (np.abs(freqs - tone_hz) > 15e3)
    if not np.any(noise_mask):
        noise_mask[:] = True
    var1 = max(float(np.mean(np.abs(X1[noise_mask]) ** 2) / n), 1e-12)
    var2 = max(float(np.mean(np.abs(X2[noise_mask]) ** 2) / n), 1e-12)

    # Bobot MRC sebanding dengan rasio amplitudo / variansi noise
    a1 = np.abs(c1)
    a2 = np.abs(c2)
    w1 = a1 / var1
    w2 = a2 / var2

    # Normalisasi bobot agar skala noise gabungan setara rata-rata noise kanal tunggal
    norm = np.sqrt(w1**2 * var1 + w2**2 * var2)
    if norm > 1e-12:
        target_noise_scale = np.sqrt(0.5 * (var1 + var2))
        w1 = (w1 / norm) * target_noise_scale
        w2 = (w2 / norm) * target_noise_scale

    # Penjumlahan koheren: sinyal saling memperkuat konstruktif 100%
    combined = w1 * x1 + w2 * x2_aligned
    return combined


def main():
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--config", default="", help="Custom config file")
    pre_args, _ = pre_parser.parse_known_args()

    cfg, cfg_file = load_config(pre_args.config)

    p = argparse.ArgumentParser(description="Pluto #1 RF RX measurement tool")
    p.add_argument("--config", default=pre_args.config, help="Path to config file (.config, .comfig, config.ini)")
    p.add_argument("--uri", default=cfg["uri"], help=f"Pluto URI (default: {cfg['uri']})")
    p.add_argument("--freq", type=float, default=cfg["freq"], help="RX center frequency in Hz")
    p.add_argument("--bw", type=float, default=cfg["bw"], help="RX RF bandwidth in Hz")
    p.add_argument("--sample-rate", type=float, default=cfg["sample_rate"], help="RX sample rate in Hz")
    p.add_argument("--rx-gain", type=float, default=cfg["rx_gain"], help="RX manual gain in dB")
    p.add_argument("--rx-channels", type=int, choices=[1, 2], default=cfg["rx_channels"], help="1=RX1, 2=RX1+RX2")
    p.add_argument("--tone", type=float, default=cfg["tone"], help="Expected baseband tone offset in Hz")
    p.add_argument("--buffer", type=int, default=cfg["buffer"], help="RX buffer size")
    p.add_argument("--interval", type=float, default=cfg["interval"], help="Seconds between measurements")
    p.add_argument("--duration", type=float, default=cfg["duration"], help="Seconds; 0 = until Ctrl+C")
    p.add_argument("--csv", default=cfg["csv"], help="Optional CSV output path")
    args = p.parse_args()

    args.uri = normalize_uri(args.uri)
    if cfg_file:
        print(f"[Config] Loaded settings from: {cfg_file}")

    if abs(args.tone) >= args.sample_rate / 2:
        raise SystemExit("--tone must be below sample-rate/2")

    print(f"Connecting to Pluto RX: {args.uri}")
    try:
        sdr = adi.ad9361(args.uri)
    except Exception:
        sdr = adi.Pluto(args.uri)

    sdr.sample_rate = int(args.sample_rate)
    sdr.rx_enabled_channels = [0] if args.rx_channels == 1 else [0, 1]
    sdr.rx_lo = int(args.freq)
    sdr.rx_rf_bandwidth = int(args.bw)
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
    history = {"RX1": []} if args.rx_channels == 1 else {"RX1": [], "RX2": [], "Combined (MRC)": []}
    try:
        while True:
            raw = sdr.rx()
            samples = raw if args.rx_channels == 2 else [raw]

            now = datetime.now().astimezone().isoformat(timespec="seconds")
            elapsed = time.monotonic() - start

            print(f"[{now}] (detik {elapsed:4.1f})")
            for idx, ch in enumerate(samples, start=1):
                m = measure_channel(
                    ch,
                    args.sample_rate,
                    args.tone,
                    noise_exclusion_hz=max(10e3, 4 * args.sample_rate / args.buffer),
                )
                ch_name = f"RX{idx}"
                history[ch_name].append(m)
                print(
                    f"  {ch_name:15}: "
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
                        "channel": ch_name,
                        "frequency_hz": int(args.freq),
                        "bandwidth_hz": int(args.bw),
                        "sample_rate_hz": int(args.sample_rate),
                        "rx_gain_db": args.rx_gain,
                        **{k: f"{v:.6f}" for k, v in m.items()},
                    })

            # Jika 2 kanal (MIMO/SIMO), hitung dan tampilkan gabungan 2 RX jadi 1 (MRC Diversity)
            if args.rx_channels == 2 and len(samples) == 2:
                comb_samples = combine_mrc(samples[0], samples[1], args.sample_rate, args.tone)
                m_comb = measure_channel(
                    comb_samples,
                    args.sample_rate,
                    args.tone,
                    noise_exclusion_hz=max(10e3, 4 * args.sample_rate / args.buffer),
                )
                history["Combined (MRC)"].append(m_comb)
                print(
                    f"  Combined (MRC) : "
                    f"signal={m_comb['signal_db']:8.2f} dB  "
                    f"noise={m_comb['noise_db']:8.2f} dB  "
                    f"SNR={m_comb['snr_db']:7.2f} dB  "
                    f"RMS={m_comb['rms_dbfs']:7.2f} dBFS  "
                    f"peak={m_comb['peak_hz']/1e3:8.2f} kHz"
                )
                if writer:
                    writer.writerow({
                        "timestamp": now,
                        "elapsed_s": f"{elapsed:.3f}",
                        "channel": "Combined_MRC",
                        "frequency_hz": int(args.freq),
                        "bandwidth_hz": int(args.bw),
                        "sample_rate_hz": int(args.sample_rate),
                        "rx_gain_db": args.rx_gain,
                        **{k: f"{v:.6f}" for k, v in m_comb.items()},
                    })

            if writer:
                csv_file.flush()

            time.sleep(args.interval)

            if args.duration > 0 and elapsed >= args.duration:
                break

    except KeyboardInterrupt:
        print("\nStopping RX test (interrupted by user)...")
    finally:
        if csv_file:
            csv_file.close()

    total_elapsed = time.monotonic() - start
    print_summary(history, total_elapsed, args.duration)


def print_summary(history: dict, total_elapsed: float, duration_target: float):
    if not history or not any(history.values()):
        print("\n[Summary] Tidak ada data pengukuran yang berhasil dicatat.")
        return

    sample_count = len(next(iter(history.values())))
    print("\n" + "=" * 70)
    print("               RINGKASAN HASIL RATA-RATA PENGUJIAN RF")
    print("=" * 70)
    target_str = f" (Target: {duration_target:.0f}s)" if duration_target > 0 else ""
    print(f"Durasi Uji: {total_elapsed:.1f} detik{target_str} | Total Sampel: {sample_count}\n")

    summary_stats = {}
    for ch_name, data in history.items():
        if not data:
            continue
        sig_avg = float(np.mean([d["signal_db"] for d in data]))
        noise_avg = float(np.mean([d["noise_db"] for d in data]))
        snr_avg = float(np.mean([d["snr_db"] for d in data]))
        rms_avg = float(np.mean([d["rms_dbfs"] for d in data]))
        summary_stats[ch_name] = {"sig": sig_avg, "noise": noise_avg, "snr": snr_avg, "rms": rms_avg}

        header = f"Kanal Gabungan: {ch_name} (2 RX Jadi 1)" if "Combined" in ch_name else f"Kanal {ch_name}"
        print(f"--- [ {header} ] ---")
        print(f"  • Signal Power Rata-rata : {sig_avg:7.2f} dB  (min: {min(d['signal_db'] for d in data):.2f}, max: {max(d['signal_db'] for d in data):.2f})")
        print(f"  • Noise Floor  Rata-rata : {noise_avg:7.2f} dB  (min: {min(d['noise_db'] for d in data):.2f}, max: {max(d['noise_db'] for d in data):.2f})")
        print(f"  • SNR          Rata-rata : {snr_avg:7.2f} dB  (min: {min(d['snr_db'] for d in data):.2f}, max: {max(d['snr_db'] for d in data):.2f})")
        print(f"  • Level ADC    Rata-rata : {rms_avg:7.2f} dBFS")

        if "Combined" in ch_name and "RX1" in summary_stats and "RX2" in summary_stats:
            d_rx1 = snr_avg - summary_stats["RX1"]["snr"]
            d_rx2 = snr_avg - summary_stats["RX2"]["snr"]
            print(f"  • Diversity Gain vs RX1  : {d_rx1:+6.2f} dB")
            print(f"  • Diversity Gain vs RX2  : {d_rx2:+6.2f} dB")
        print()

    print("=" * 70)
    print("Nilai di atas siap disalin ke TABEL_PENGUJIAN_RF.md")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
