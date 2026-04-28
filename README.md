# ESP32-CAM Smart Door Lock & Face Recognition System

[Türkçe](#türkçe) | [English](#english)

---

## Türkçe

Bu proje, ESP32-CAM ve Python kullanarak geliştirilmiş, canlılık testi (liveness detection) ve Telegram entegrasyonu özelliklerine sahip akıllı bir kapı kilidi sistemidir.

### 🚀 Özellikler

- **Yüz Tanıma:** Bilinen kişileri %99 doğrulukla tanır.
- **Canlılık Testi (Liveness Detection):** Fotoğraf ile kandırılmayı önlemek için göz kırpma kontrolü yapar.
- **Mesafe Sensörü:** Birisi kapıya yaklaştığında (HC-SR04) sistemi otomatik aktif eder.
- **Gece Modu:** Ortam karanlıksa ESP32-CAM üzerindeki flaşı otomatik açar.
- **Telegram Entegrasyonu:** Tanınmayan birisi geldiğinde fotoğrafını Telegram'a gönderir ve "Aç", "Kaydet ve Aç" veya "Reddet" seçeneklerini sunar.
- **Sesli Geri Bildirim:** Edge-TTS kullanarak kullanıcıya sesli komutlar verir.
- **Servo Kontrolü:** Onay verildiğinde kapı kilidini (servo) fiziksel olarak açar.

### 🛠️ Donanım Gereksinimleri

- ESP32-CAM Modülü
- FTDI Programlayıcı (Yükleme için)
- HC-SR04 Ultrasonik Mesafe Sensörü
- Servo Motor (Örn: SG90 veya MG995)
- Jumper Kablolar ve Breadboard

### 💻 Yazılım Kurulumu

1. **ESP32-CAM:** `esp32cam/esp32.ino` dosyasını Arduino IDE ile açın, WiFi bilgilerinizi girin ve kartınıza yükleyin.
2. **Python Bağımlılıkları:** Bilgisayarınızda şu kütüphanelerin yüklü olduğundan emin olun:
   ```bash
   pip install opencv-python numpy face_recognition pyTelegramBotAPI edge-tts pygame scipy nest_asyncio
   ```
3. **Yapılandırma:** `main.py` dosyasını açın ve aşağıdaki alanları kendi bilgilerinizle doldurun:
   - `ESP_IP`: ESP32'nin aldığı IP adresi.
   - `TELEGRAM_TOKEN`: BotFather'dan aldığınız token.
   - `CHAT_ID`: Bildirimlerin geleceği Telegram ID'niz.

### 📂 Dosya Yapısı

- `main.py`: Ana Python kontrol merkezi.
- `esp32cam/esp32.ino`: ESP32-CAM firmware kodu.
- `yuzler/`: Tanınacak kişilerin klasörleri (Klasör ismi = Kişi ismi).
- `.gitignore`: Gereksiz dosyaların takibini önler.

### 🛡️ Güvenlik Notu
Bu proje eğitim amaçlıdır. Gerçek dünya güvenlik uygulamaları için ek şifreleme ve güvenlik katmanları eklenmesi önerilir.

---

## English

This project is a smart door lock system developed using ESP32-CAM and Python, featuring liveness detection and Telegram integration.

### 🚀 Features

- **Face Recognition:** Recognizes known individuals with high accuracy.
- **Liveness Detection:** Performs blink detection to prevent spoofing with photos.
- **Distance Sensor:** Automatically activates the system when someone approaches the door (using HC-SR04).
- **Night Mode:** Automatically turns on the ESP32-CAM flash in low-light conditions.
- **Telegram Integration:** Sends photos of unrecognized individuals to Telegram and offers "Open", "Save & Open", or "Reject" options.
- **Voice Feedback:** Provides voice commands using Edge-TTS.
- **Servo Control:** Physically opens the door lock (servo) once authorized.

### 🛠️ Hardware Requirements

- ESP32-CAM Module
- FTDI Programmer (for uploading code)
- HC-SR04 Ultrasonic Distance Sensor
- Servo Motor (e.g., SG90 or MG995)
- Jumper Wires & Breadboard

### 💻 Software Setup

1. **ESP32-CAM:** Open `esp32cam/esp32.ino` in Arduino IDE, enter your WiFi credentials, and upload it to your board.
2. **Python Dependencies:** Ensure you have the following libraries installed:
   ```bash
   pip install opencv-python numpy face_recognition pyTelegramBotAPI edge-tts pygame scipy nest_asyncio
   ```
3. **Configuration:** Open `main.py` and fill in the following fields with your own information:
   - `ESP_IP`: The IP address assigned to your ESP32.
   - `TELEGRAM_TOKEN`: The token provided by BotFather.
   - `CHAT_ID`: Your Telegram ID where notifications will be sent.

### 📂 File Structure

- `main.py`: Main Python control center.
- `esp32cam/esp32.ino`: ESP32-CAM firmware code.
- `yuzler/`: Folders for recognized individuals (Folder name = Person's name).
- `.gitignore`: Prevents tracking of unnecessary files.

### 🛡️ Security Note
This project is for educational purposes. For real-world security applications, adding extra encryption and security layers is recommended.

---
Developed by: **Berat Keskin**
