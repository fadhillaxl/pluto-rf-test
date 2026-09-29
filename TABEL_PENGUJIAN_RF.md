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
| **1** | **SISO Tanpa SPF** *(Baseline)* | TX: OFF<br>RX: OFF | **RX1** | *... dB* | *... dB* | *... dB* | *... dBFS* | `0.00 dB` *(Ref)* | ☐ Baik  ☐ Lemah |
| **2** | **SISO dengan SPF (TX + RX)** | TX: ON (SPF1)<br>RX1: ON (SPF2) | **RX1** | *... dB* | *... dB* | *... dB* | *... dBFS* | *... dB* | ☐ Baik  ☐ Overload |
| **3** | **MIMO Tanpa SPF** | TX: OFF<br>RX: OFF | **RX1** | *... dB* | *... dB* | *... dB* | *... dBFS* | *... dB* | ☐ Baik  ☐ Lemah |
| | | | **RX2** | *... dB* | *... dB* | *... dB* | *... dBFS* | *... dB* | ☐ Baik  ☐ Lemah |
| **4** | **MIMO dengan SPF (RX1 + RX2)** | TX: OFF<br>RX1: ON (SPF1)<br>RX2: ON (SPF2) | **RX1** | *... dB* | *... dB* | *... dB* | *... dBFS* | *... dB* | ☐ Baik  ☐ Overload |
| | | | **RX2** | *... dB* | *... dB* | *... dB* | *... dBFS* | *... dB* | ☐ Baik  ☐ Overload |

---

## 4. Tabel Lembar Kerja Pengujian Lapangan (Multi-Run Logging)

Catat setiap percobaan (minimal 3 kali pengulangan) untuk mengantisipasi deviasi fluktuasi sinyal:

### Pengujian 1: SISO Tanpa SPF5189Z
- **Parameter**: Frekuensi: `434 MHz`, BW: `1 MHz`, Sample Rate: `2 MSPS`, TX Gain: `-20 dB`, RX Gain: `30 dB`
- **Output CSV**: `T1_siso_no_spf.csv`

| Run | Timestamp | Signal (dB) | Noise (dB) | SNR (dB) | RMS (dBFS) | Peak Offset (kHz) | Catatan Kondisi |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|---|
| #1 | | | | | | | |
| #2 | | | | | | | |
| #3 | | | | | | | |
| **Rata-rata** | | | | | | | |

---

### Pengujian 2: SISO dengan SPF5189Z (TX + RX)
- **Parameter**: Frekuensi: `434 MHz`, BW: `1 MHz`, Sample Rate: `2 MSPS`, TX Gain: `-20 dB`, RX Gain: `30 dB`
- **Output CSV**: `T2_siso_spf_tx_rx.csv`

| Run | Timestamp | Signal (dB) | Noise (dB) | SNR (dB) | RMS (dBFS) | Peak Offset (kHz) | Catatan Kondisi |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|---|
| #1 | | | | | | | |
| #2 | | | | | | | |
| #3 | | | | | | | |
| **Rata-rata** | | | | | | | |

---

### Pengujian 3: MIMO / SIMO Tanpa SPF5189Z (RX1 & RX2)
- **Parameter**: Frekuensi: `434 MHz`, BW: `1 MHz`, Sample Rate: `2 MSPS`, TX Gain: `-20 dB`, RX Gain: `30 dB`
- **Output CSV**: `T3_simo_no_spf.csv`

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

### Skenario 1 — SISO Tanpa SPF
```bash
# Terminal 1 (TX - Pluto #2):
python tx.py --uri ip:192.168.2.11 --freq 434e6 --bw 1e6 --sample-rate 2e6 --tx-gain -20 --tone 100e3

# Terminal 2 (RX - Pluto #1):
python rx_test.py --uri ip:192.168.2.10 --freq 434e6 --bw 1e6 --sample-rate 2e6 --rx-gain 30 --rx-channels 1 --duration 60 --csv T1_siso_no_spf.csv
```

### Skenario 2 — SISO dengan SPF (TX + RX)
```bash
# Terminal 1 (TX - Pluto #2 -> SPF #1):
python tx.py --uri ip:192.168.2.11 --freq 434e6 --bw 1e6 --sample-rate 2e6 --tx-gain -20 --tone 100e3

# Terminal 2 (SPF #2 -> Pluto #1 RX1):
python rx_test.py --uri ip:192.168.2.10 --freq 434e6 --bw 1e6 --sample-rate 2e6 --rx-gain 30 --rx-channels 1 --duration 60 --csv T2_siso_spf_tx_rx.csv
```

### Skenario 3 — MIMO Tanpa SPF
```bash
# Terminal 1 (TX - Pluto #2):
python tx.py --uri ip:192.168.2.11 --freq 434e6 --bw 1e6 --sample-rate 2e6 --tx-gain -20 --tone 100e3

# Terminal 2 (Pluto #1 RX1 + RX2):
python rx_test.py --uri ip:192.168.2.10 --freq 434e6 --bw 1e6 --sample-rate 2e6 --rx-gain 30 --rx-channels 2 --duration 60 --csv T3_simo_no_spf.csv
```

### Skenario 4 — MIMO dengan SPF (RX1 + RX2)
```bash
# Terminal 1 (TX - Pluto #2):
python tx.py --uri ip:192.168.2.11 --freq 434e6 --bw 1e6 --sample-rate 2e6 --tx-gain -20 --tone 100e3

# Terminal 2 (Pluto #1 RX1[SPF1] + RX2[SPF2]):
python rx_test.py --uri ip:192.168.2.10 --freq 434e6 --bw 1e6 --sample-rate 2e6 --rx-gain 30 --rx-channels 2 --duration 60 --csv T4_simo_spf_rx1_rx2.csv
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
