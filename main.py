import cv2
import urllib.request
import numpy as np
import face_recognition
import os
import time
import telebot
from telebot import types
from datetime import datetime
import asyncio
import edge_tts             
import nest_asyncio         
import pygame
from scipy.spatial import distance as dist 

# ==========================================
# 🛠️ KULLANICI AYARLARI (GitHub için temizlendi)
# ==========================================
ESP_IP = 'ESP_IP_ADRESINIZ'   # Örn: '192.168.1.50'
TELEGRAM_TOKEN = 'BOT_TOKENINIZ' 
CHAT_ID = 'CHAT_ID_NUMARANIZ'      
MESAFE_SINIRI = 10          # Kaç cm yakında yüz taransın?

VOICE = "tr-TR-EmelNeural"
EYE_AR_THRESH = 0.23 

# 🔥 TOLERANS: (0.6 = Gevşek, 0.3 = Çok Sıkı)
TOLERANCE_LEVEL = 0.40 

# 🌑 GECE MODU AYARLARI
PARLAKLIK_SINIRI = 80   
FLAS_GUCU = 150         
# ==========================================

nest_asyncio.apply()

url_capture = f'http://{ESP_IP}/capture'
url_action = f'http://{ESP_IP}/action?go=kapiac'
url_status = f'http://{ESP_IP}/status'
url_flash = f'http://{ESP_IP}/control?var=led_intensity&val={{}}'

path = 'yuzler'

try: pygame.mixer.init()
except: print("⚠️ Ses sistemi hatası.")

try:
    bot = telebot.TeleBot(TELEGRAM_TOKEN)
    bot.get_updates(offset=-1)
    print("✅ Telegram Botu Hazır!")
except Exception as e: print("❌ Telegram Bot Hatası:", e)

# ==========================================
# 📂 YÜZ VERİTABANI YÜKLEME
# ==========================================
print("📂 Yüz veritabanı yükleniyor...")
known_face_encodings = []
known_face_names = []

if not os.path.exists(path): os.makedirs(path)

for isim_klasoru in os.listdir(path):
    if isim_klasoru.startswith('.'): continue
    klasor_yolu = os.path.join(path, isim_klasoru)
    if os.path.isdir(klasor_yolu):
        kisi_ismi = isim_klasoru.upper() 
        for resim_adi in os.listdir(klasor_yolu):
            if resim_adi.endswith(('.jpg', '.png', '.jpeg')):
                img_path = os.path.join(klasor_yolu, resim_adi)
                try:
                    img = face_recognition.load_image_file(img_path)
                    encs = face_recognition.face_encodings(img)
                    if encs:
                        known_face_encodings.append(encs[0])
                        known_face_names.append(kisi_ismi)
                except: pass
        print(f"   ✅ Yüklendi: {kisi_ismi}")

print(f"✅ Toplam {len(known_face_names)} yüz verisi hafızada.")
print("-" * 50)
print(f"📡 SİSTEM AKTİF! ({ESP_IP})...")

# --- YARDIMCI FONKSİYONLAR ---

def parlaklik_hesapla(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return np.mean(gray)

def flas_kontrol(acik_mi):
    try:
        val = FLAS_GUCU if acik_mi else 0
        urllib.request.urlopen(url_flash.format(val), timeout=1)
    except: pass

def goz_orani_hesapla(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

async def ses_kaydet_async(metin):
    communicate = edge_tts.Communicate(metin, VOICE)
    await communicate.save("temp_ses.mp3")

def sesli_soyle(metin, bekle=True):
    print(f"🗣️ Asistan: '{metin}'")
    try:
        asyncio.run(ses_kaydet_async(metin))
        pygame.mixer.music.load("temp_ses.mp3")
        pygame.mixer.music.play()
        if bekle:
            while pygame.mixer.music.get_busy(): time.sleep(0.1)
            pygame.mixer.music.unload()
    except: pass

def get_image():
    try:
        # Önceki capture'ı temizlemek için bir kez boş istek atıyoruz (ESP32-CAM buffer temizliği)
        try: urllib.request.urlopen(url_capture, timeout=0.5); time.sleep(0.1)
        except: pass
        img_resp = urllib.request.urlopen(url_capture, timeout=4)
        imgnp = np.array(bytearray(img_resp.read()), dtype=np.uint8)
        img = cv2.imdecode(imgnp, -1)
        return img
    except: return None

def kapiyi_ac():
    try: urllib.request.urlopen(url_action, timeout=1); print("🚪 Kapı Açılıyor...")
    except: pass

def telegramdan_secim_iste(foto_dosyasi):
    print("📨 Telegram'a soruluyor...")
    try:
        markup = types.InlineKeyboardMarkup()
        btn_ac = types.InlineKeyboardButton("✅ Sadece Aç", callback_data="kapi_ac")
        btn_kaydet = types.InlineKeyboardButton("💾 Kaydet ve Aç", callback_data="kapi_kaydet")
        btn_red = types.InlineKeyboardButton("⛔ Reddet", callback_data="kapi_kilit")
        markup.row(btn_ac)
        markup.row(btn_kaydet)
        markup.row(btn_red)
        
        with open(foto_dosyasi, 'rb') as photo:
            sent_msg = bot.send_photo(CHAT_ID, photo, caption="⚠️ TANINMAYAN KİŞİ! Ne yapayım?", reply_markup=markup)
        
        print("⏳ Cevap bekleniyor...")
        start_time = time.time()
        
        while (time.time() - start_time) < 30:
            try:
                updates = bot.get_updates(offset=-1, timeout=1) 
                if updates:
                    last = updates[-1]
                    if last.callback_query and last.callback_query.message.message_id == sent_msg.message_id:
                        call = last.callback_query
                        data = call.data
                        bot.answer_callback_query(call.id, "İşlem yapılıyor...")

                        if data == "kapi_ac":
                            bot.edit_message_caption(chat_id=CHAT_ID, message_id=call.message.message_id, caption="✅ KAPI AÇILDI (Kaydedilmedi)", reply_markup=None)
                            return "AC"
                        elif data == "kapi_kaydet":
                            bot.edit_message_caption(chat_id=CHAT_ID, message_id=call.message.message_id, caption="💾 KAYDEDİLDİ VE AÇILDI", reply_markup=None)
                            return "KAYDET"
                        elif data == "kapi_kilit":
                            bot.edit_message_caption(chat_id=CHAT_ID, message_id=call.message.message_id, caption="⛔ REDDEDİLDİ", reply_markup=None)
                            return "RED"
            except Exception as e: print(f"Telegram Loop Hatası: {e}")
            time.sleep(0.5) 
        
        try: bot.edit_message_caption(chat_id=CHAT_ID, message_id=sent_msg.message_id, caption="⏰ ZAMAN AŞIMI", reply_markup=None)
        except: pass
        return "RED"
    except Exception as e: return "RED"

def canlilik_testi_yap(beklenen_kisi):
    print(f"👀 CANLILIK TESTİ BAŞLIYOR: {beklenen_kisi}")
    sesli_soyle(f"Merhaba {beklenen_kisi}. Güvenlik için lütfen yavaşça göz kırpın.", bekle=True)
    baslangic = time.time()
    
    while (time.time() - baslangic) < 10:
        img = get_image()
        if img is None: continue
        
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        landmarks_list = face_recognition.face_landmarks(rgb_img)
        
        if not landmarks_list: continue 
            
        anlik_encodings = face_recognition.face_encodings(rgb_img)
        kimlik_dogrulandi = False
        if anlik_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, anlik_encodings[0], tolerance=TOLERANCE_LEVEL)
            if True in matches:
                face_distances = face_recognition.face_distance(known_face_encodings, anlik_encodings[0])
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    anlik_isim = known_face_names[best_match_index]
                    if anlik_isim == beklenen_kisi:
                        kimlik_dogrulandi = True
        
        if not kimlik_dogrulandi:
            print("⚠️ Kimlik doğrulanamadı (Maske/Yabancı Şüphesi)!")
            continue 

        test_basarili = False
        for landmarks in landmarks_list:
            left_eye = landmarks['left_eye']
            right_eye = landmarks['right_eye']
            leftEAR = goz_orani_hesapla(left_eye)
            rightEAR = goz_orani_hesapla(right_eye)
            avgEAR = (leftEAR + rightEAR) / 2.0
            print(f"👁️ Göz Oranı: {avgEAR:.2f} (Limit: {EYE_AR_THRESH}) - Kimlik: OK", end='\r')
            if avgEAR < EYE_AR_THRESH: test_basarili = True
        
        if test_basarili:
            print("\n✅ GÖZ KIRPMA VE KİMLİK ONAYLANDI!")
            sesli_soyle("Teşekkürler, giriş onaylandı.")
            return True
        
        if cv2.waitKey(1) & 0xFF == ord('q'): break
            
    print("\n❌ ZAMAN AŞIMI veya KİMLİK HATASI.")
    sesli_soyle("Kimlik doğrulanamadı. Lütfen yüzünüzü net gösterin.")
    return False

# --- ANA DÖNGÜ ---
cv2.namedWindow("Kapi Kamerasi", cv2.WINDOW_AUTOSIZE)
flas_acik_mi = False

while True:
    try:
        try:
            resp = urllib.request.urlopen(url_status, timeout=1)
            veri = resp.read().decode('utf-8').strip()
            mesafe = int(veri) if veri.isdigit() else 999
        except: mesafe = 999
        
        print(f"Mesafe: {mesafe} cm   ", end='\r') 

        if 0 < mesafe < MESAFE_SINIRI:
            print(f"\n🏃 HAREKET! ({mesafe} cm)")
            img = get_image()
            if img is None: continue
            
            parlaklik = parlaklik_hesapla(img)
            if parlaklik < PARLAKLIK_SINIRI and not flas_acik_mi:
                print(f"🌑 KARANLIK ({parlaklik:.1f}) -> FLAŞ AÇIK 💡")
                flas_kontrol(True)
                flas_acik_mi = True
                time.sleep(0.5) 
                img = get_image() 

            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            face_encs = face_recognition.face_encodings(rgb_img)

            if not face_encs:
                print("👀 Yüz YOK. Görmezden geliniyor.")
                if flas_acik_mi:
                    flas_kontrol(False)
                    flas_acik_mi = False
                cv2.imshow("Kapi Kamerasi", img)
                cv2.waitKey(100)
                continue 

            isim = "BILINMIYOR"
            taniyan_var = False

            matches = face_recognition.compare_faces(known_face_encodings, face_encs[0], tolerance=TOLERANCE_LEVEL)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encs[0])
            best_match_index = np.argmin(face_distances) 

            if matches[best_match_index]:
                isim = known_face_names[best_match_index]
                taniyan_var = True
            
            cv2.putText(img, f"DURUM: {isim}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            cv2.imshow("Kapi Kamerasi", img)
            cv2.waitKey(100) 

            # --- KARAR MERKEZİ ---
            if taniyan_var:
                if canlilik_testi_yap(isim):
                    kapiyi_ac()
                    time.sleep(4)
            
            else: 
                print(f"🚨 YABANCI!")
                sesli_soyle("Sizi tanıyamadım, haber veriyorum.")
                cv2.imwrite("supheli.jpg", img)
                cevap = telegramdan_secim_iste("supheli.jpg")
                
                if cevap == "AC":
                    sesli_soyle("Kapı açılıyor.")
                    kapiyi_ac()
                    time.sleep(4)
                elif cevap == "KAYDET":
                    sesli_soyle("Sizi kaydettim, kapıyı açıyorum.")
                    
                    zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
                    yeni_klasor = os.path.join(path, f"MISAFIR_{zaman_damgasi}")
                    if not os.path.exists(yeni_klasor): os.makedirs(yeni_klasor)
                    
                    cv2.imwrite(os.path.join(yeni_klasor, "kayit.jpg"), img)
                    known_face_encodings.append(face_encs[0])
                    known_face_names.append(f"MISAFIR_{zaman_damgasi}")
                    
                    kapiyi_ac()
                    time.sleep(4)
                else:
                    sesli_soyle("Reddedildi.")

            print("💤 Bekleniyor...")
            if flas_acik_mi:
                flas_kontrol(False)
                flas_acik_mi = False
            time.sleep(3) 

        else:
            time.sleep(0.5)

        if cv2.waitKey(1) & 0xFF == ord('q'): break
    except KeyboardInterrupt: 
        if flas_acik_mi: flas_kontrol(False)
        break
    except Exception as e: print(f"Hata: {e}"); time.sleep(1)

cv2.destroyAllWindows()
