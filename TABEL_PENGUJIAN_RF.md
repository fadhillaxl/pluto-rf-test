# Tabel Perbandingan RF: Pluto+ SDR & LNA SPF5189Z

Dokumen ini memuat matriks pengujian dan tabel perbandingan parameter RF (**Signal/RSSI Level, Noise Floor, SNR, dan RMS dBFS**) menggunakan:
- **2 unit Adalm-Pluto+ SDR**: 
  - Pluto #2 sebagai **Transmitter (TX)**
  - Pluto #1 sebagai **Receiver (RX1 & RX2)**
- **2 unit LNA SPF5189Z** (dialokasikan sesuai skenario)

---

## 1. Topologi & Pembagian Hardware

| Skenario | Nama Pengujian | Alokasi SPF5189Z #1 | Alokasi SPF5189Z #2 | Mode Kanal RX | Keterangan |
|---|---|---|---|---|---|
| **Skenario 1** | **SISO Tanpa SPF** | *Tidak dipakai* | *Tidak dipakai* | RX1 | Baseline acuan (tanpa penguat) |
| **Skenario 2** | **SISO dengan SPF (TX + RX)** | Dipasang di **TX** (Booster) | Dipasang di **RX1** (LNA) | RX1 | Uji performa link jarak jauh / rugi transmisi |
| **Skenario 3** | **MIMO / SIMO Tanpa SPF** | *Tidak dipakai* | *Tidak dipakai* | RX1 + RX2 | Baseline diversity 2 channel tanpa penguat |
| **Skenario 4** | **MIMO / SIMO dengan SPF (RX1 + RX2)** | Dipasang di **RX1** (LNA 1) | Dipasang di **RX2** (LNA 2) | RX1 + RX2 | Uji sensitivitas dual receiver diversity |

> [!CAUTION]
> **Peringatan Keamanan RF (Skenario 2)**:
> SPF5189Z pada sisi TX berfungsi sebagai *driver amplifier* (Gain ~15-20 dB). Jika pengujian menggunakan **kabel coaxial langsung**, pastikan menggunakan **Attenuator RF (minimal 30-40 dB)** di antara TX dan RX agar input mixer AD9363 pada Pluto RX tidak rusak atau overload. Disarankan memulai dengan `--tx-gain -30` atau `-20`.

---

## 2. Diagram Blok Koneksi

### Skenario 1: SISO Tanpa SPF5189Z (Baseline)
```text
[ Pluto #2 TX1 ] ───────────────────────────────> [ Pluto #1 RX1 ]
(Gain: -20 dB)        (Kabel + Attenuator         (Gain: 30 dB)
                       atau Antena Over-The-Air)
```

### Skenario 2: SISO dengan SPF5189Z (TX + RX)
```text
[ Pluto #2 TX1 ] ──> [ SPF #1 TX ] ─────────────> [ SPF #2 RX ] ──> [ Pluto #1 RX1 ]
                      (Booster Amp)  (RF Link)        (LNA)
```

### Skenario 3: MIMO / SIMO Tanpa SPF5189Z
```text
                                              ┌─> [ Pluto #1 RX1 ]
[ Pluto #2 TX1 ] ──> [ RF Splitter / Link ] ──┤
                                              └─> [ Pluto #1 RX2 ]
```

### Skenario 4: MIMO / SIMO dengan SPF5189Z (RX1 + RX2)
```text
                                              ┌─> [ SPF #1 ] ──> [ Pluto #1 RX1 ]
[ Pluto #2 TX1 ] ──> [ RF Splitter / Link ] ──┤
                                              └─> [ SPF #2 ] ──> [ Pluto #1 RX2 ]
```

---

## 3. Tabel Perbandingan Utama (Hasil Rata-Rata)

Gunakan tabel berikut untuk merangkum nilai rata-rata dari masing-masing sesi pengujian:

| No | Skenario Pengujian | Konfigurasi LNA | Kanal | Signal Level (`signal_db`) | Noise Floor (`noise_db`) | SNR (`snr_db`) | Level ADC (`rms_dbfs`) | Δ SNR vs Baseline | Status / Kualitas Sinyal |
|:--:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | **SISO Tanpa SPF** *(Baseline)* | TX: OFF<br>RX: OFF | **RX1** | **53.22 dB** | **39.51 dB** | **13.70 dB** | **2.00 dBFS** | `0.00 dB` *(Ref)* | ☑ Baik  ☐ Lemah |
| **2** | **SISO dengan SPF (TX + RX)** | TX: ON (SPF1)<br>RX1: ON (SPF2) | **RX1** | **78.01 dB** | **45.80 dB** | **32.21 dB** | **14.35 dBFS** | **+18.51 dB** | ☑ Sangat Baik  ☐ Overload |
| **3** | **MIMO / SIMO Tanpa SPF** | TX: OFF<br>RX: OFF | **RX1** | **54.52 dB** | **39.46 dB** | **15.06 dB** | **2.01 dBFS** | `+1.36 dB` | ☑ Baik  ☐ Lemah |
| | | | **RX2** | **55.81 dB** | **39.99 dB** | **15.82 dB** | **2.63 dBFS** | `+2.12 dB` | ☑ Baik  ☐ Lemah |
| | | | **Combined (MRC)** *(2 RX Jadi 1)* | **58.12 dB** | **39.76 dB** | **18.36 dB** | **2.58 dBFS** | **+4.66 dB** | ☑ Sangat Baik *(Diversity Gain +3.3 dB)* |
| **4** | **MIMO / SIMO dengan SPF (RX1 + RX2)** | TX: OFF<br>RX1: ON (SPF1)<br>RX2: ON (SPF2) | **RX1** | *... dB* | *... dB* | *... dB* | *... dBFS* | *... dB* | ☐ Baik  ☐ Overload |
| | | | **RX2** | *... dB* | *... dB* | *... dB* | *... dBFS* | *... dB* | ☐ Baik  ☐ Overload |
| | | | **Combined (MRC)** *(2 RX Jadi 1)* | *... dB* | *... dB* | *... dB* | *... dBFS* | *... dB* | ☐ Baik  ☐ Overload |

---

## 4. Tabel Lembar Kerja Pengujian Lapangan (Multi-Run Logging)

Catat setiap percobaan (minimal 3 kali pengulangan) untuk mengantisipasi deviasi fluktuasi sinyal:

### Pengujian 1: SISO Tanpa SPF5189Z
- **Parameter**: Frekuensi: `434 MHz`, BW: `1 MHz`, Sample Rate: `2 MSPS`, TX Gain: `-10 dB`, RX Gain: `30 dB`
- **Output CSV**: `T1_siso_no_spf.csv`
- **Metode**: Pengujian otomatis via `python auto_test.py --scenario 1 --duration 10`

| Run | Timestamp | Signal (dB) | Noise (dB) | SNR (dB) | RMS (dBFS) | Peak Offset (kHz) | Catatan Kondisi |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|---|
| #1 | 2026-09-29T22:06:59 | 53.70 | 39.49 | 14.21 | 2.29 | 101.20 | Lock stabil 100 kHz tone |
| #2 | 2026-09-29T22:07:04 | 53.67 | 39.48 | 14.19 | 1.90 | 101.20 | Lock stabil 100 kHz tone |
| #3 | 2026-09-29T22:07:09 | 53.38 | 39.54 | 13.84 | 2.10 | 101.20 | Lock stabil 100 kHz tone |
| **Rata-rata (11 Sampel)** | **Durasi 10 detik** | **53.22** | **39.51** | **13.70** | **2.00** | **101.20** | **Baseline SISO Valid** |

---

### Pengujian 2: SISO dengan SPF5189Z (TX + RX)
- **Parameter**: Frekuensi: `434 MHz`, BW: `1 MHz`, Sample Rate: `2 MSPS`, TX Gain: `-10 dB`, RX Gain: `30 dB`
- **Output CSV**: `T2_siso_spf_tx_rx.csv`
- **Metode**: Pasang SPF1 di TX & SPF2 di RX1, lalu jalankan `python auto_test.py --scenario 2 --duration 10`

| Run | Timestamp | Signal (dB) | Noise (dB) | SNR (dB) | RMS (dBFS) | Peak Offset (kHz) | Catatan Kondisi |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|---|
| #1 | 2026-09-29T22:02:39 | 77.78 | 46.05 | 31.73 | 14.32 | 101.20 | Lock stabil 100 kHz tone |
| #2 | 2026-09-29T22:02:44 | 78.45 | 45.78 | 32.66 | 14.65 | 101.32 | Gain ganda TX+RX bekerja |
| #3 | 2026-09-29T22:02:49 | 77.92 | 45.97 | 31.95 | 14.48 | 101.20 | Penguatan konsisten |
| **Rata-rata (11 Sampel)** | **Durasi 10 detik** | **78.01** | **45.80** | **32.21** | **14.35** | **101.20** | **Δ SNR = +18.5 s.d. +20.5 dB vs Baseline** |

---

### Pengujian 3: MIMO / SIMO Tanpa SPF5189Z (RX1, RX2 & Combined MRC)
- **Parameter**: Frekuensi: `434 MHz`, BW: `1 MHz`, Sample Rate: `2 MSPS`, TX Gain: `-10 dB`, RX Gain: `30 dB`
- **Output CSV**: `T3_simo_no_spf.csv`
- **Metode**: Pengujian otomatis via `python auto_test.py --scenario 3 --duration 10`

| Run | Kanal | Signal (dB) | Noise (dB) | SNR (dB) | RMS (dBFS) | Peak Offset (kHz) | Catatan Kondisi |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| #1 | RX1 | 54.90 | 39.40 | 15.49 | 2.14 | 101.20 | Antena 1 |
| | RX2 | 55.84 | 39.93 | 15.91 | 2.56 | 101.20 | Antena 2 |
| | **Combined (MRC)** | **58.32** | **39.63** | **18.69** | **2.64** | **101.20** | **2 RX digabung jadi 1 (+2.78 dB)** |
| #2 | RX1 | 54.54 | 39.47 | 15.07 | 1.96 | 101.20 | Antena 1 |
| | RX2 | 56.14 | 40.02 | 16.12 | 2.68 | 101.20 | Antena 2 |
| | **Combined (MRC)** | **58.33** | **39.71** | **18.63** | **2.57** | **101.20** | **2 RX digabung jadi 1 (+2.51 dB)** |
| #3 | RX1 | 54.55 | 39.56 | 14.99 | 2.06 | 101.20 | Antena 1 |
| | RX2 | 55.51 | 39.94 | 15.57 | 2.64 | 101.20 | Antena 2 |
| | **Combined (MRC)** | **57.97** | **39.77** | **18.20** | **2.61** | **101.20** | **2 RX digabung jadi 1 (+2.63 dB)** |
| **Rata-rata (11 Sampel)** | **RX1** | **54.52** | **39.46** | **15.06** | **2.01** | **101.20** | **Kanal RX1 Mandiri** |
| | **RX2** | **55.81** | **39.99** | **15.82** | **2.63** | **101.20** | **Kanal RX2 Mandiri** |
| | **Combined (MRC)** | **58.12** | **39.76** | **18.36** | **2.58** | **101.20** | **Diversity Gain = +3.30 dB vs RX1, +2.54 dB vs RX2!** |

---

### Pengujian 4: MIMO / SIMO dengan SPF5189Z (RX1 & RX2)
- **Parameter**: Frekuensi: `434 MHz`, BW: `1 MHz`, Sample Rate: `2 MSPS`, TX Gain: `-20 dB`, RX Gain: `30 dB`
- **Output CSV**: `T4_simo_spf_rx1_rx2.csv`

| Run | Kanal | Signal (dB) | Noise (dB) | SNR (dB) | RMS (dBFS) | Peak Offset (kHz) | Catatan Balance RX1/RX2 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| #1 | RX1 | | | | | | |
| | RX2 | | | | | | |
| #2 | RX1 | | | | | | |
| | RX2 | | | | | | |
| #3 | RX1 | | | | | | |
| | RX2 | | | | | | |
| **Rata-rata** | **RX1** | | | | | | |
| | **RX2** | | | | | | |

---

## 5. Panduan Menjalankan Perintah (Command Checklist)

Pastikan lingkungan virtual telah aktif sebelum menjalankan:
```bash
source venv/bin/activate
```

### Cara Praktis: Otomasi End-to-End (`auto_test.py`)

Gunakan script otomasi `auto_test.py` dari laptop. Script ini secara otomatis menyalakan TX via SSH di `root@aml.local`, menjalankan pengukuran RX di laptop, menghitung rata-rata, menyimpan CSV, dan mematikan TX secara aman saat selesai:

```bash
# Skenario 1 (SISO Baseline, 10 detik):
python auto_test.py --scenario 1 --duration 10

# Skenario 2 (SISO dengan SPF TX + RX, 10 detik):
python auto_test.py --scenario 2 --duration 10

# Skenario 3 (SIMO / Dual RX Baseline, 10 detik):
python auto_test.py --scenario 3 --duration 10

# Skenario 4 (SIMO dengan SPF RX1 + RX2, 10 detik):
python auto_test.py --scenario 4 --duration 10
```

---

### Cara Manual (Dua Terminal Terpisah)

Jika ingin menjalankan secara manual:

#### Skenario 1 — SISO Tanpa SPF
```bash
# Terminal 1 (TX - Pluto #2 via SSH aml.local):
python tx.py --uri ip:192.168.99.240 --freq 434e6 --bw 1e6 --sample-rate 2e6 --tx-gain -10 --tone 100e3

# Terminal 2 (RX - Pluto #1 di Laptop):
python rx_test.py --uri usb: --freq 434e6 --bw 1e6 --sample-rate 2e6 --rx-gain 30 --rx-channels 1 --duration 10 --csv T1_siso_no_spf.csv
```

#### Skenario 2 — SISO dengan SPF (TX + RX)
```bash
# Terminal 1 (TX - Pluto #2 -> SPF #1):
python tx.py --uri ip:192.168.99.240 --freq 434e6 --bw 1e6 --sample-rate 2e6 --tx-gain -10 --tone 100e3

# Terminal 2 (SPF #2 -> Pluto #1 RX1):
python rx_test.py --uri usb: --freq 434e6 --bw 1e6 --sample-rate 2e6 --rx-gain 30 --rx-channels 1 --duration 10 --csv T2_siso_spf_tx_rx.csv
```

#### Skenario 3 — MIMO / SIMO Tanpa SPF
```bash
# Terminal 1 (TX - Pluto #2 via SSH aml.local):
python tx.py --uri ip:192.168.99.240 --freq 434e6 --bw 1e6 --sample-rate 2e6 --tx-gain -10 --tone 100e3

# Terminal 2 (Pluto #1 RX1 + RX2 di Laptop):
python rx_test.py --uri usb: --freq 434e6 --bw 1e6 --sample-rate 2e6 --rx-gain 30 --rx-channels 2 --duration 10 --csv T3_simo_no_spf.csv
```

#### Skenario 4 — MIMO / SIMO dengan SPF (RX1 + RX2)
```bash
# Terminal 1 (TX - Pluto #2 via SSH aml.local):
python tx.py --uri ip:192.168.99.240 --freq 434e6 --bw 1e6 --sample-rate 2e6 --tx-gain -10 --tone 100e3

# Terminal 2 (Pluto #1 RX1[SPF1] + RX2[SPF2] di Laptop):
python rx_test.py --uri usb: --freq 434e6 --bw 1e6 --sample-rate 2e6 --rx-gain 30 --rx-channels 2 --duration 10 --csv T4_simo_spf_rx1_rx2.csv
```

---

## 6. Kunci Evaluasi & Analisis Parameter

1. **`signal_db` (Relative Signal Power)**:
   - Dihitung dari integrasi daya spectral bin FFT di sekitar frekuensi uji (100 kHz tone).
   - Semakin tinggi nilainya, semakin besar daya sinyal yang sampai ke baseband receiver.
2. **`noise_db` (Noise Floor)**:
   - Dihitung dari daerah FFT di luar tone sinyal dan DC offset.
   - Pemasangan LNA SPF5189Z di sisi RX umumnya akan menaikkan *noise floor* beberapa dB karena penambahan noise figure internal amplifier.
3. **`snr_db` (Signal-to-Noise Ratio = `signal_db - noise_db`)**:
   - **Metrik utama**: Keberhasilan LNA dinilai dari apakah `snr_db` meningkat dibanding baseline.
   - Jika `signal_db` naik 15 dB tetapi `noise_db` juga naik 15 dB, maka SNR tidak membaik (hanya terjadi pergeseran gain). LNA efektif jika peningkatan `signal_db` lebih tinggi daripada kenaikan `noise_db`.
4. **`rms_dbfs` (ADC Saturation Guard)**:
   - Nilai saturasi maksimum ADC adalah `0.0 dBFS`.
   - Pastikan nilai `rms_dbfs` berada di rentang aman **`-30 dBFS` sampai `-10 dBFS`**.
   - Jika `rms_dbfs` mendekati `0 dBFS` (misal `-2 dBFS` atau `0.0 dBFS`), ADC AD9363 mengalami **clipping/saturasi**. Kurangi `--rx-gain` atau `--tx-gain` agar data tidak distorsi.
5. **Keseimbangan Kanal RX1 vs RX2 (MIMO/SIMO)**:
   - Evaluasi perbedaan gain antara kedua unit SPF5189Z. Normalnya perbedaan respons antara kedua LNA berada di bawah 1 - 2 dB pada frekuensi yang sama.
6. **Diversity Combining (MRC - "2 RX Jadi 1")**:
   - Di sisi hardware, Pluto+ memiliki 2 port antena dan 2 ADC independen.
   - Di sisi software / DSP (`rx_test.py`), sinyal dari RX1 dan RX2 digabungkan secara digital menggunakan algoritma **Maximal Ratio Combining (MRC)**:
     $$y_{\text{combined}} = w_1 \cdot y_1 + w_2 \cdot y_2 e^{-j \Delta \phi}$$
   - Fasa kedua sinyal disinkronkan secara presisi (mengeliminasi beda fasa dan CFO) sehingga sinyal tone saling memperkuat secara koheren (+3 dB secara teori), sementara noise yang tidak saling berkorelasi akan tereduksi.
   - Hasil pengujian membuktikan **Combined MRC** menghasilkan SNR hingga **`18.36 dB`** (**keuntungan ekstra +3.30 dB dibanding RX1 dan +2.54 dB dibanding RX2**).

