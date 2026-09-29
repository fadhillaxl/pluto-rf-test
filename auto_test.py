#!/usr/bin/env python3
"""
Otomasi Pengujian RF End-to-End Pluto+ SDR
- Remote (TX): Pluto #2 via SSH ke root@aml.local (atau host pilihan)
- Local  (RX): Pluto #1 via USB pada Laptop

Penggunaan:
  # Jalankan Skenario 1 (SISO Tanpa SPF, 10 detik):
  python auto_test.py --scenario 1

  # Jalankan Skenario 3 (SIMO/MIMO Tanpa SPF, 10 detik):
  python auto_test.py --scenario 3

  # Jalankan dengan parameter kustom:
  python auto_test.py --scenario 1 --duration 10 --tx-gain -10 --rx-gain 30
"""

import argparse
import subprocess
import sys
import time
import signal

SCENARIO_CONFIG = {
    "1": {
        "name": "Skenario 1 - SISO Tanpa SPF5189Z (Baseline)",
        "csv": "T1_siso_no_spf.csv",
        "channels": 1,
        "desc": "TX Pluto #2 (No SPF) -> RX1 Pluto #1 (No SPF)"
    },
    "2": {
        "name": "Skenario 2 - SISO dengan SPF5189Z (TX + RX)",
        "csv": "T2_siso_spf_tx_rx.csv",
        "channels": 1,
        "desc": "TX Pluto #2 -> SPF TX -> Link -> SPF RX -> RX1 Pluto #1"
    },
    "3": {
        "name": "Skenario 3 - SIMO / Dual RX Tanpa SPF5189Z",
        "csv": "T3_simo_no_spf.csv",
        "channels": 2,
        "desc": "TX Pluto #2 (No SPF) -> RX1 + RX2 Pluto #1 (No SPF)"
    },
    "4": {
        "name": "Skenario 4 - SIMO / Dual RX dengan SPF5189Z",
        "csv": "T4_simo_spf_rx1_rx2.csv",
        "channels": 2,
        "desc": "TX Pluto #2 -> Link -> SPF RX1 & SPF RX2 -> Pluto #1"
    },
}


def stop_remote_tx(remote_host, remote_dir):
    """Menghentikan proses tx.py pada SBC remote."""
    cmd = [
        "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
        remote_host,
        f"killall -9 python 2>/dev/null || pkill -f 'tx.py' 2>/dev/null || true"
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    except Exception as e:
        print(f"[Warning] Gagal menghentikan remote TX: {e}", file=sys.stderr)


def start_remote_tx(remote_host, remote_dir, tx_gain, freq, bw, sample_rate, tone):
    """Menjalankan tx.py di SBC remote di background."""
    print(f"[TX Remote] Memulai transmisi sinyal di {remote_host}...")
    
    # Pastikan proses lama mati
    stop_remote_tx(remote_host, remote_dir)
    time.sleep(0.5)

    tx_cmd = (
        f"cd {remote_dir} && "
        f"source venv/bin/activate 2>/dev/null || true; "
        f"nohup {remote_dir}/venv/bin/python tx.py "
        f"--tx-gain {tx_gain} "
        f"--freq {freq} "
        f"--bw {bw} "
        f"--sample-rate {sample_rate} "
        f"--tone {tone} "
        f"> tx.log 2>&1 & sleep 1; pgrep -f 'tx.py' | head -n 1"
    )

    ssh_cmd = [
        "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8",
        remote_host,
        tx_cmd
    ]

    res = subprocess.run(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    pid = res.stdout.strip()
    if not pid:
        # Cek log jika gagal
        check_log = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", remote_host, f"cat {remote_dir}/tx.log"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        raise RuntimeError(f"Gagal memulai tx.py di {remote_host}.\nLog output:\n{check_log.stdout}\n{check_log.stderr}")

    print(f"[TX Remote] TX Aktif (PID: {pid}) | Freq={freq/1e6:.3f}MHz | Gain={tx_gain}dB | Tone={tone/1e3:.1f}kHz")
    return pid


def main():
    parser = argparse.ArgumentParser(description="Otomasi Pengujian RF End-to-End Pluto+ SDR (TX Remote + RX Laptop)")
    parser.add_argument("--scenario", "-s", choices=["1", "2", "3", "4", "T1", "T2", "T3", "T4"], default="1",
                        help="Pilih skenario pengujian (1-4 atau T1-T4)")
    parser.add_argument("--remote-host", default="root@aml.local", help="SSH remote TX host (default: root@aml.local)")
    parser.add_argument("--remote-dir", default="/root/pluto-rf-test", help="Path direktori di host remote")
    parser.add_argument("--channels", "-c", type=int, choices=[1, 2], default=None,
                        help="Jumlah kanal RX (1=RX1, 2=RX1+RX2). Default sesuai skenario.")
    parser.add_argument("--duration", "-d", type=float, default=10.0,
                        help="Durasi pengujian dalam detik (default: 10s)")
    parser.add_argument("--tx-gain", type=float, default=-10.0, help="TX Gain pada Pluto #2 (default: -10 dB)")
    parser.add_argument("--rx-gain", type=float, default=30.0, help="RX Gain pada Pluto #1 (default: 30 dB)")
    parser.add_argument("--freq", type=float, default=434000000, help="Frekuensi LO RF dalam Hz (default: 434 MHz)")
    parser.add_argument("--bw", type=float, default=1000000, help="Bandwidth RF dalam Hz (default: 1 MHz)")
    parser.add_argument("--sample-rate", type=float, default=2000000, help="Sample rate dalam Hz (default: 2 MSPS)")
    parser.add_argument("--tone", type=float, default=100000, help="Offset tone IF dalam Hz (default: 100 kHz)")
    parser.add_argument("--csv", default="", help="Nama file CSV output (default otomatis dari skenario)")

    args = parser.parse_args()

    # Normalisasi skenario ID
    scen_key = args.scenario.replace("T", "")
    scen_info = SCENARIO_CONFIG.get(scen_key, SCENARIO_CONFIG["1"])

    rx_channels = args.channels if args.channels is not None else scen_info["channels"]
    csv_file = args.csv if args.csv else scen_info["csv"]

    print("\n" + "="*70)
    print("           PENGUJIAN RF OTOMATIS: PLUTO+ SDR")
    print("="*70)
    print(f"Skenario     : {scen_info['name']}")
    print(f"Deskripsi    : {scen_info['desc']}")
    print(f"TX Host      : {args.remote_host} (Pluto #2)")
    print(f"RX Host      : Laptop Lokal (Pluto #1)")
    print(f"Frekuensi    : {args.freq/1e6:.6f} MHz")
    print(f"Kanal RX     : {'RX1 + RX2' if rx_channels == 2 else 'RX1'}")
    print(f"TX Gain      : {args.tx_gain:.1f} dB | RX Gain: {args.rx_gain:.1f} dB")
    print(f"Durasi Uji   : {args.duration:.1f} detik")
    print(f"Output CSV   : {csv_file}")
    print("="*70 + "\n")

    tx_pid = None
    try:
        # 1. Mulai Remote TX
        tx_pid = start_remote_tx(
            remote_host=args.remote_host,
            remote_dir=args.remote_dir,
            tx_gain=args.tx_gain,
            freq=args.freq,
            bw=args.bw,
            sample_rate=args.sample_rate,
            tone=args.tone
        )

        # Beri jeda 1 detik agar sinyal stabil sebelum RX mulai mengukur
        time.sleep(1.0)

        # 2. Jalankan RX Lokal
        rx_cmd = [
            sys.executable, "rx_test.py",
            "--freq", str(args.freq),
            "--bw", str(args.bw),
            "--sample-rate", str(args.sample_rate),
            "--tone", str(args.tone),
            "--rx-gain", str(args.rx_gain),
            "--rx-channels", str(rx_channels),
            "--duration", str(args.duration),
            "--csv", csv_file
        ]

        print(f"\n[RX Lokal] Memulai penerima sinyal & pengukuran ({args.duration}s)...")
        rx_proc = subprocess.run(rx_cmd)

    except KeyboardInterrupt:
        print("\n[Pengujian Dibatalkan oleh Pengguna (Ctrl+C)]")
    except Exception as e:
        print(f"\n[Error] Terjadi kesalahan: {e}", file=sys.stderr)
    finally:
        # 3. Selalu pastikan remote TX dimatikan
        print(f"\n[TX Remote] Menghentikan transmitter di {args.remote_host}...")
        stop_remote_tx(args.remote_host, args.remote_dir)
        print("[Selesai] TX telah dihentikan. Pengujian selesai aman.\n")


if __name__ == "__main__":
    main()
