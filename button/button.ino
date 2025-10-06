// ==== PENGATURAN PIN ====
#define BUTTON_PIN 12
#define BUZZER_PIN 19

// ==== PENGATURAN BAUD RATE ====
#define BAUD_RATE 9600

// ==== Variabel untuk Debounce Tombol Non-Blocking ====
unsigned long lastSendTime = 0; // Waktu terakhir kita mengirim sinyal 's'
const long sendDelay = 200;     // Jeda waktu antar pengiriman (200 milidetik)

// ==== Variabel untuk Buzzer Non-Blocking ====
bool isBuzzerActive = false;        // Status untuk menandakan buzzer sedang menyala
unsigned long buzzerStartTime = 0;  // Waktu kapan buzzer mulai menyala
const long buzzerDuration = 6000;   // Durasi buzzer menyala dalam milidetik (1000ms = 1 detik)

void setup() {
  Serial.begin(BAUD_RATE);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  // Inisialisasi pin buzzer sebagai OUTPUT
  pinMode(BUZZER_PIN, OUTPUT);
  // Pastikan buzzer dalam keadaan mati saat program dimulai
  digitalWrite(BUZZER_PIN, LOW); 
  
  Serial.println("ESP32 siap (versi dengan buzzer)...");
  delay(1000);
}

void loop() {
  // === BAGIAN 1: FUNGSI TOMBOL (KODE ASLI ANDA) ===
  // Kode ini tetap berjalan seperti biasa untuk mengirim 's' saat tombol ditekan.
  if (digitalRead(BUTTON_PIN) == LOW) {
    if ((millis() - lastSendTime) > sendDelay) {
      Serial.println('s');
      lastSendTime = millis(); 
    }
  }

  // === BAGIAN 2: MENERIMA PERINTAH SERIAL UNTUK BUZZER ===
  // Cek apakah ada data masuk di port serial.
  if (Serial.available() > 0) {
    char receivedChar = Serial.read(); // Baca karakter yang masuk
    
    // Jika karakter yang diterima adalah 'b'
    if (receivedChar == 'b') {
      Serial.println("Karakter 'b' diterima, menyalakan buzzer...");
      isBuzzerActive = true;        // Aktifkan flag buzzer
      buzzerStartTime = millis();   // Catat waktu kapan buzzer mulai menyala
      digitalWrite(BUZZER_PIN, HIGH); // Nyalakan buzzer
    }
  }

  // === BAGIAN 3: MENGELOLA TIMER BUZZER (NON-BLOCKING) ===
  // Bagian ini akan selalu dieksekusi setiap loop.
  // Cek HANYA jika flag buzzer sedang aktif DAN sudah melewati durasi yang ditentukan.
  if (isBuzzerActive && (millis() - buzzerStartTime >= buzzerDuration)) {
    digitalWrite(BUZZER_PIN, LOW); // Matikan buzzer
    isBuzzerActive = false;        // Non-aktifkan flag agar pengecekan ini tidak dijalankan lagi
    // Serial.println("Buzzer dimatikan secara otomatis.");
  }
}