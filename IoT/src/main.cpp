#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "Wokwi-GUEST";        // atau ganti ke WiFi kamu
const char* password = "";               // password WiFi
String serverUrl = "https://pseudoepiscopal-alvaro-winy.ngrok-free.dev/receive_sensor"; // atau URL ngrok kamu

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  Serial.print("Connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi connected!");
}

void loop() {
  float suhu = random(250, 350) / 10.0;
  float kelembapan = random(400, 800) / 10.0;
  float kualitas_udara = random(0, 100);

  HTTPClient http;
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");

  String payload = "{\"temperature\":" + String(suhu, 2) +
                   ",\"humidity\":" + String(kelembapan, 2) +
                   ",\"air_quality\":" + String(kualitas_udara, 2) + "}";

  int code = http.POST(payload);
  Serial.printf("Data: %s\nResponse: %d\n\n", payload.c_str(), code);
  http.end();

  delay(5000);
}
