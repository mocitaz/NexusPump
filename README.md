# Bot Saham IDX Telegram (Python) 🚀

Bot Telegram untuk analisis teknikal, chart, dan alert saham Indonesia (IDX) secara live menggunakan `python-telegram-bot` dan `yfinance`.

## Fitur
- **Harga Live**: `/harga BBCA` (Cek harga, change%, volume, H/L)
- **Chart Candle**: `/chart TLKM 3mo` (Chart dengan MA20, MA50, Volume)
- **Analisa Teknikal**: `/analisa GOTO` (RSI, MACD, Bollinger Bands, Sinyal)
- **Prediksi Simple**: `/predict ANTM` (Linear Regression 7 hari kedepan)
- **Top Gainers/Losers**: `/gainers` dan `/losers`
- **Auto Alert**: Notifikasi otomatis ke channel jika ada saham di watchlist naik signifikikan.

## Instalasi Lokal

1.  **Clone Repository**
    ```bash
    git clone <repo_url>
    cd BotTele
    ```

2.  **Buat Virtual Environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Mac/Linux
    # venv\Scripts\activate   # Windows
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Konfigurasi Environment**
    Set environment variable berikut (atau edit langsung di `main.py` walau tidak disarankan untuk production):
    - `TELEGRAM_BOT_TOKEN`: Token dari @BotFather
    - `TELEGRAM_CHANNEL_ID`: ID Channel untuk alerts (misal `@channel_saham_gw`)

5.  **Jalankan Bot**
    ```bash
    python3 main.py
    ```

## Cara Hosting (Gratis/Murah)

### Opsi 1: Render.com (Recommended)
1.  Buat akun di [Render.com](https://render.com).
2.  Klik **New +** -> **Background Worker** (Agar bot jalan terus).
    *   *Note: Free tier Render akan sleep jika Web Service, tapi Background Worker berbayar. Untuk gratis, coba "Web Service" tapi gunakan cron-job ping, atau gunakan Railway.*
    *   **Alternatif Gratis Terbaik**: **Railway.app** (Trial) atau local server (Raspberry Pi).

### Opsi 2: Railway.app
1.  Buat project baru di Railway.
2.  Connect GitHub repo ini.
3.  Add Variable: `TELEGRAM_BOT_TOKEN` dan `TELEGRAM_CHANNEL_ID`.
4.  Railway akan otomatis mendeteksi `requirements.txt` dan `Procfile` (jika ada) atau menjalankan `python main.py`.
5.  **Command Start**: `python3 main.py`

### Opsi 3: VPS (DigitalOcean / AWS EC2)
1.  Sewa VPS termurah ($5/mo).
2.  Install Python & Git.
3.  Clone repo & Install requirements.
4.  Jalankan dengan `nohup` atau `systemd` agar monitoring jalan terus 24/7.
    ```bash
    nohup python3 main.py &
    ```

## Struktur Project
- `main.py`: Logic utama bot & scheduler.
- `data_fetcher.py`: Ambil data dari Yahoo Finance.
- `analyzer.py`: Hitung indikator teknikal.
- `chart_generator.py`: Buat gambar chart candlestick.
- `alerts.py`: Logic monitoring background.

## Disclaimer
Bot ini hanya alat bantu informasi (Not Financial Advice). Data saham memiliki delay 15 menit (keterbatasan yfinance free).
