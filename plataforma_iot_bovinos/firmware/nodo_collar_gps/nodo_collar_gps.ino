/*
 * ============================================================================
 * Proyecto de Tesis: Monitoreo GPS de Bovinos - Valle del Mezquital, Hidalgo
 * Nodo 1: Collar Emisor (Heltec LoRa ESP32 v2 + GPS)
 * Autor: Iván Rodríguez Hernández - Maestría Mecatrónica ITESHU
 * ============================================================================
 */

#include <SPI.h>
#include <LoRa.h>
#include <TinyGPS++.h>
#include <HardwareSerial.h>
#include "config.h"

// Pines SPI de LoRa integrados en tarjeta Heltec LoRa ESP32 v2
#define SCK_LORA    5
#define MISO_LORA   19
#define MOSI_LORA   27
#define SS_LORA     18
#define RST_LORA    14
#define DIO0_LORA   26

TinyGPSPlus gps;
HardwareSerial gpsSerial(1);

unsigned long ultimoEnvio = 0;
uint32_t contadorPaquetes = 0;

// Lectura de batería aproximada en porcentaje (0-100%)
int leerBateriaPct() {
  int adc = analogRead(PIN_BATERIA);
  float voltaje = (adc / 4095.0) * 3.3 * 2.0; // Divisor 1:2
  int pct = (int)((voltaje - 3.2) / (4.2 - 3.2) * 100.0);
  if (pct > 100) pct = 100;
  if (pct < 0) pct = 0;
  return pct;
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n[NODO 1 - COLLAR BOVINO] Inicializando...");

  // Inicialización de puerto Serial para GPS
  gpsSerial.begin(GPS_BAUD_RATE, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
  Serial.println("[GPS] Puerto serie iniciado en pines 22/23 a 9600 baudios.");

  // Configuración de pines SPI para módulo LoRa SX1276 interno de Heltec
  SPI.begin(SCK_LORA, MISO_LORA, MOSI_LORA, SS_LORA);
  LoRa.setPins(SS_LORA, RST_LORA, DIO0_LORA);

  if (!LoRa.begin(BAND)) {
    Serial.println("[ERROR CRÍTICO] Fallo al inicializar el radio LoRa a 915MHz.");
    while (1);
  }

  LoRa.setTxPower(LORA_TX_POWER);
  LoRa.setSpreadingFactor(LORA_SPREADING);
  LoRa.setSignalBandwidth(LORA_BW);
  LoRa.setSyncWord(0x34); // Palabra de sincronía privada
  Serial.println("[LoRa] Radio configurado en 915 MHz (Canal Privado).");
  Serial.println("[SISTEMA] Listo. Esperando coordenadas GPS...");
}

void loop() {
  // Lectura continua y no bloqueante del buffer serie del GPS
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }

  // Verificación de intervalo no bloqueante usando millis()
  unsigned long tiempoActual = millis();
  if (tiempoActual - ultimoEnvio >= INTERVALO_ENVIO_MS) {
    ultimoEnvio = tiempoActual;
    contadorPaquetes++;

    bool fixValido = gps.location.isValid();
    double latitud = fixValido ? gps.location.lat() : 20.37542; // Coordenada de prueba si no hay fix en laboratorio
    double longitud = fixValido ? gps.location.lng() : -99.65431;
    float altitud = gps.altitude.isValid() ? gps.altitude.meters() : 2105.0;
    float velocidad = gps.speed.isValid() ? gps.speed.kmph() : 0.0;
    int satelites = gps.satellites.isValid() ? gps.satellites.value() : 0;
    int bateria = leerBateriaPct();

    // Construcción de trama compacta para transmisión LoRa:
    // FORMATO: ID_DEV,ID_ANIMAL,LAT,LON,ALT,VEL,BAT,SATS,FIX_OK,PKT_SEQ
    char tramaLoRa[160];
    snprintf(tramaLoRa, sizeof(tramaLoRa),
      "%s,%s,%.6f,%.6f,%.1f,%.1f,%d,%d,%d,%u",
      DEVICE_ID,
      ANIMAL_ID,
      latitud,
      longitud,
      altitud,
      velocidad,
      bateria,
      satelites,
      fixValido ? 1 : 0,
      contadorPaquetes
    );

    // Enviar paquete LoRa
    LoRa.beginPacket();
    LoRa.print(tramaLoRa);
    LoRa.endPacket();

    Serial.print("[LoRa TX] Paquete #");
    Serial.print(contadorPaquetes);
    Serial.print(" enviado: ");
    Serial.println(tramaLoRa);
  }
}
