# Pluto+ RF RSSI / SNR Test

Project untuk menguji hubungan RF antara:

- **Pluto #2 = transmitter**
- **Pluto #1 = receiver / measurement instrument**

Pengujian dapat dilakukan sebagai:

1. SISO: Pluto #2 TX -> Pluto #1 RX1
2. SIMO: Pluto #2 TX -> Pluto #1 RX1 + RX2
3. Dengan atau tanpa SPF5189Z

> Penting: `signal_db`, `noise_db`, dan SNR pada script ini adalah **pengukuran relatif dari IQ/FFT**, bukan RSSI dBm yang sudah dikalibrasi. Untuk perbandingan A/B, gunakan frekuensi, gain, bandwidth, sample rate, kabel, antena, jarak, dan kondisi lingkungan yang sama.

## 1. Arsitektur

### SISO tanpa SPF

```text
Pluto #2 TX ----------------------> Pluto #1 RX1
                                      |
                                      +--> RSSI/SNR
```

### SISO dengan SPF TX + RX

```text
Pluto #2 TX -> SPF #1 -> RF link -> SPF #2 -> Pluto #1 RX1
```

### SIMO tanpa SPF

```text
                         +--------> Pluto #1 RX1
Pluto #2 TX -> RF split -+
                         +--------> Pluto #1 RX2
```

### SIMO dengan SPF pada RX1/RX2

```text
                         +-> SPF #1 -> RX1
Pluto #2 TX -> RF split -+
                         +-> SPF #2 -> RX2
```

**Jangan menghubungkan satu TX langsung ke dua RX menggunakan kabel Y sederhana.**
Gunakan splitter/coupler RF yang sesuai untuk eksperimen kabel.

## 2. Catatan keselamatan RF

Saat pengujian melalui kabel:

- Gunakan attenuator RF yang sesuai antara TX dan RX.
- Jangan memasukkan level RF yang terlalu besar ke input RX.
- SPF5189Z dapat meningkatkan level sinyal dan dapat membuat RX overload.
- Mulai dari TX gain rendah.
- Untuk pengujian antena, jangan gunakan koneksi kabel tanpa memperhitungkan level daya dan isolasi.
- Pastikan frekuensi dan antena sesuai dengan band yang digunakan.

## 3. Struktur project

```text
pluto-rf-test/
├── tx.py
├── rx_test.py
├── requirements.txt
└── README.md
```

## 4. Instalasi

Disarankan Python 3.10--3.13 pada Raspberry Pi.

```bash
git clone <your-repository>
cd pluto-rf-test

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

`pyadi-iio` memerlukan `libiio` di sistem.

Pada Raspberry Pi Debian/Ubuntu:

```bash
sudo apt update
sudo apt install -y libiio-utils libiio-dev
```

Cek Pluto:

```bash
iio_info -s
```

Jika Pluto terhubung lewat USB, URI dapat berupa sesuatu seperti:

```text
usb:0
```

Jika lewat network:

```text
ip:192.168.2.10
```

Sesuaikan IP dengan jaringan Pluto kamu.

## 5. Jalankan transmitter — Pluto #2

Contoh:

```bash
python3 tx.py \
  --uri ip:192.168.2.11 \
  --freq 434e6 \
  --bw 1e6 \
  --sample-rate 2e6 \
  --tx-gain -20 \
  --tone 100e3
```

Parameter penting:

```text
--uri
--freq
--bw
--sample-rate
--tx-gain
--tone
--buffer
--duration
```

Contoh 915 MHz:

```bash
python3 tx.py \
  --uri ip:192.168.2.11 \
  --freq 915e6 \
  --bw 2e6 \
  --sample-rate 4e6 \
  --tx-gain -30
```

TX berjalan continuous sampai `Ctrl+C`.

## 6. Jalankan receiver — Pluto #1 RX1

```bash
python3 rx_test.py \
  --uri ip:192.168.2.10 \
  --freq 434e6 \
  --bw 1e6 \
  --sample-rate 2e6 \
  --rx-gain 30 \
  --rx-channels 1
```

Output kira-kira:

```text
=== Pluto RX TEST ===
Frequency    : 434.000000 MHz
Bandwidth    : 1.000 MHz
Sample rate  : 2.000 MSPS
RX gain      : 30.0 dB
RX channels  : RX1

[2026-09-29T20:00:01+07:00]
  RX1: signal=  82.31 dB  noise=  55.14 dB  SNR=  27.17 dB RMS= -34.21 dBFS peak=  100.01 kHz
```

Angka `signal` dan `noise` bukan dBm. Yang paling penting untuk A/B adalah perubahan **SNR** dan perubahan relatif level sinyal.

## 7. Test RX1 + RX2

```bash
python3 rx_test.py \
  --uri ip:192.168.2.10 \
  --freq 434e6 \
  --bw 1e6 \
  --sample-rate 2e6 \
  --rx-gain 30 \
  --rx-channels 2
```

Output:

```text
RX1: signal=... noise=... SNR=...
RX2: signal=... noise=... SNR=...
```

Ini adalah mode **1 TX -> 2 RX (SIMO)**.

Script ini belum melakukan combining RX1/RX2. RX1 dan RX2 dilaporkan secara terpisah agar efek SPF dan masing-masing RF chain dapat dibandingkan.

## 8. Simpan hasil ke CSV

RX1:

```bash
python3 rx_test.py \
  --uri ip:192.168.2.10 \
  --freq 434e6 \
  --bw 1e6 \
  --sample-rate 2e6 \
  --rx-gain 30 \
  --rx-channels 1 \
  --duration 60 \
  --csv test_siso.csv
```

RX1 + RX2:

```bash
python3 rx_test.py \
  --uri ip:192.168.2.10 \
  --freq 434e6 \
  --bw 1e6 \
  --sample-rate 2e6 \
  --rx-gain 30 \
  --rx-channels 2 \
  --duration 60 \
  --csv test_simo.csv
```

## 9. Test matrix untuk 2 SPF5189Z

Gunakan parameter TX/RX yang sama.

### T1 — SISO tanpa SPF

```text
Pluto #2 TX -> Pluto #1 RX1
```

```bash
python3 rx_test.py --uri ip:192.168.2.10 \
  --freq 434e6 --bw 1e6 --sample-rate 2e6 \
  --rx-gain 30 --rx-channels 1 \
  --duration 60 --csv T1_siso_no_spf.csv
```

### T2 — SISO SPF TX + RX

```text
Pluto #2 TX -> SPF #1 -> link -> SPF #2 -> Pluto #1 RX1
```

Jalankan TX dengan parameter yang sama, kemudian RX:

```bash
python3 rx_test.py --uri ip:192.168.2.10 \
  --freq 434e6 --bw 1e6 --sample-rate 2e6 \
  --rx-gain 30 --rx-channels 1 \
  --duration 60 --csv T2_siso_spf.csv
```

### T3 — SIMO tanpa SPF

```text
Pluto #2 TX -> splitter/coupler -> RX1 + RX2
```

```bash
python3 rx_test.py --uri ip:192.168.2.10 \
  --freq 434e6 --bw 1e6 --sample-rate 2e6 \
  --rx-gain 30 --rx-channels 2 \
  --duration 60 --csv T3_simo_no_spf.csv
```

### T4 — SIMO SPF RX1 + RX2

```text
                 +-> SPF #1 -> RX1
TX -> splitter --+
                 +-> SPF #2 -> RX2
```

```bash
python3 rx_test.py --uri ip:192.168.2.10 \
  --freq 434e6 --bw 1e6 --sample-rate 2e6 \
  --rx-gain 30 --rx-channels 2 \
  --duration 60 --csv T4_simo_spf.csv
```

## 10. Tabel hasil

Gabungkan hasil menjadi:

| Test | SPF TX | SPF RX1 | SPF RX2 | RX1 RSSI/Level | RX1 SNR | RX2 RSSI/Level | RX2 SNR |
|---|---:|---:|---:|---:|---:|---:|---:|
| T1 SISO | No | No | - | | | - | - |
| T2 SISO | Yes | Yes | - | | | - | - |
| T3 SIMO | No | No | No | | | | |
| T4 SIMO | No | Yes | Yes | | | | |

## 11. Penting tentang RSSI dBm

Script ini sengaja tidak mengklaim `signal_db` sebagai dBm.

Kalau kamu ingin tabel seperti:

```text
RSSI = -67.4 dBm
Noise = -92.1 dBm
SNR = 24.7 dB
```

kita perlu menambahkan metode kalibrasi RX dan/atau membaca atribut RSSI yang disediakan driver AD9363 sesuai konfigurasi Pluto. Nilai ADC/FFT sendiri adalah nilai relatif.

Untuk eksperimen SPF5189Z, metode relatif tetap sangat berguna jika seluruh kondisi pengukuran dikunci.

## 12. Rekomendasi urutan pengujian

1. Pastikan T1 bekerja.
2. Catat baseline selama 60 detik.
3. Tambahkan SPF TX + RX untuk T2.
4. Kembalikan ke tanpa SPF dan aktifkan RX2 untuk T3.
5. Tambahkan dua SPF pada RX1/RX2 untuk T4.
6. Jangan mengubah `rx-gain` antar-test.
7. Jangan mengubah TX gain antar-test.
8. Jangan mengubah frequency/bandwidth/sample rate.
9. Gunakan kabel, attenuator, splitter, dan antena yang sama.
10. Ulangi setiap test minimal 3 kali jika ingin hasil yang lebih dapat dibandingkan.

## 13. Pengembangan berikutnya

Project ini dapat dikembangkan menjadi:

- calibrated RSSI dBm
- automatic SPF A/B test
- automatic T1--T4 test runner
- BER / packet error rate
- QPSK/OFDM test waveform
- throughput measurement
- RX1/RX2 diversity combining
- CSV + Excel report
- real-time web dashboard
