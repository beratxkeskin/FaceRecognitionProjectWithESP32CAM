#include "esp_camera.h"
#include <WiFi.h>
#include <ESP32Servo.h>

// ==========================================
// KULLANICI AYARLARI
// ==========================================
const char* ssid = "WIFI_ADINIZ";
const char* password = "WIFI_SIFRENIZ";
// ==========================================

Servo kapiServosu;

#define SERVO_PIN 14
#define TRIG_PIN 13
#define ECHO_PIN 15

// AI THINKER Pinleri
#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27
#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22

WiFiServer server(80);

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  // Sensör ve motor ayarları
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  kapiServosu.setPeriodHertz(50);
  kapiServosu.attach(SERVO_PIN, 500, 2400);
  kapiServosu.write(0);
  delay(1000);
  kapiServosu.detach();

  // Kamera ayarları
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if (psramFound()) {
    config.frame_size = FRAMESIZE_VGA;
    config.jpeg_quality = 10;
    config.fb_count = 1;
  } else {
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  esp_camera_init(&config);

  sensor_t* s = esp_camera_sensor_get();
  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);
    s->set_brightness(s, 1);
    s->set_saturation(s, -2);
  }

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.print("http://");
  Serial.println(WiFi.localIP());

  server.begin();
}

// Mesafe ölçme fonksiyonu
int mesafeyi_olcu() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long sure = pulseIn(ECHO_PIN, HIGH);
  int mesafe = sure * 0.034 / 2;
  return mesafe;
}

void loop() {
  WiFiClient client = server.available();

  if (client) {
    String currentLine = "";
    String request = "";

    unsigned long timeout = millis() + 3000;

    while (client.connected() && millis() < timeout) {
      if (client.available()) {
        char c = client.read();
        request += c;

        if (c == '\n') {
          if (currentLine.length() == 0) {

            // FOTOĞRAF
            if (request.indexOf("GET /capture") >= 0) {
              camera_fb_t* fb = esp_camera_fb_get();
              if (!fb) {
                client.println("HTTP/1.1 500 Internal Server Error");
                client.stop();
                return;
              }

              client.println("HTTP/1.1 200 OK");
              client.println("Content-Type: image/jpeg");
              client.println("Content-Disposition: inline; filename=capture.jpg");
              client.println("Access-Control-Allow-Origin: *");
              client.println();

              client.write(fb->buf, fb->len);
              client.println();
              esp_camera_fb_return(fb);
            }

            // KAPI AÇ
            else if (request.indexOf("GET /action?go=kapiac") >= 0) {
              kapiServosu.attach(SERVO_PIN);
              kapiServosu.write(180);
              delay(4000);
              kapiServosu.write(0);
              delay(1000);
              kapiServosu.detach();

              client.println("HTTP/1.1 200 OK");
              client.print("Kapi Acildi");
            }

            // MESAFE
            else if (request.indexOf("GET /status") >= 0) {
              int anlik_mesafe = mesafeyi_olcu();

              client.println("HTTP/1.1 200 OK");
              client.println("Content-Type: text/plain");
              client.println("Access-Control-Allow-Origin: *");
              client.println();

              client.print(anlik_mesafe);
            }

            break;
          } else {
            currentLine = "";
          }
        } else if (c != '\r') {
          currentLine += c;
        }
      }
    }
    client.stop();
  }
}