/*
 * ============================================================================
 * Proyecto de Tesis: Monitoreo GPS de Bovinos - Valle del Mezquital, Hidalgo
 * Nodo 2: Gateway Retransmisor (Heltec LoRa ESP32 v2 -> Wi-Fi -> MQTT)
 * Autor: Iván Rodríguez Hernández - Maestría Mecatrónica ITESHU
 * ============================================================================
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <SPI.h>
#include <LoRa.h>
#include "config.h"

// Pines SPI de LoRa integrados en tarjeta Heltec LoRa ESP32 v2
#define SCK_LORA    5
#define MISO_LORA   19
#define MOSI_LORA   27
#define SS_LORA     18
#define RST_LORA    14
#define DIO0_LORA   26

WiFiClient espClient;
PubSubClient mqttClient(espClient);

// Fail-safe de posición: conservar la última coordenada válida recibida por LoRa.
char ultimaLatValida[16] = "";
char ultimaLonValida[16] = "";
bool hayFixValido = false;

// Compuerta no bloqueante para reintentos MQTT (prohibido delay() en loop()).
unsigned long ultimoIntentoMQTT = 0;

void setupWiFi() {
  delay(10);
  Serial.print("\n[WIFI] Conectando a ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int intentos = 0;
  while (WiFi.status() != WL_CONNECTED && intentos < 20) {
    delay(500);
    Serial.print(".");
    intentos++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WIFI] Conexión establecida.");
    Serial.print("[WIFI] IP asignada: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[WIFI] Advertencia: No se pudo conectar a la red WiFi.");
  }
}

void reconectarMQTT() {
  if (WiFi.status() != WL_CONNECTED || mqttClient.connected()) return;

  // Un solo intento por ciclo como máximo, espaciado por millis().
  // Así la recepción LoRa no se bloquea mientras el broker esté caído.
  unsigned long ahora = millis();
  if (ahora - ultimoIntentoMQTT < 3000) return;
  ultimoIntentoMQTT = ahora;

  Serial.print("[MQTT] Conectando al broker en ");
  Serial.print(MQTT_BROKER_HOST);
  Serial.print("...");

  String clientId = "Gateway-Heltec-";
  clientId += String(random(0xffff), HEX);

  // Conexión con Last Will and Testament
  if (mqttClient.connect(clientId.c_str(), MQTT_USER, MQTT_PASS, MQTT_TOPIC_LWT, 1, true, "{\"estado\":\"offline\"}")) {
    Serial.println(" ¡Conectado!");
    mqttClient.publish(MQTT_TOPIC_LWT, "{\"estado\":\"online\"}", true);
  } else {
    Serial.print(" Falló, rc=");
    Serial.print(mqttClient.state());
    Serial.println(". Reintentaré en 3 s sin bloquear el loop.");
  }
}

void procesarPaqueteLoRa(int packetSize) {
  if (packetSize == 0) return;

  String mensajeRecibido = "";
  while (LoRa.available()) {
    mensajeRecibido += (char)LoRa.read();
  }

  int rssi = LoRa.packetRssi();
  float snr = LoRa.packetSnr();

  Serial.println("\n--- [LoRa RX] Paquete Detectado ---");
  Serial.print("Payload crudo: ");
  Serial.println(mensajeRecibido);
  Serial.print("RSSI: "); Serial.print(rssi); Serial.print(" dBm | SNR: "); Serial.println(snr);

  // Parsear trama: ID_DEV,ID_ANIMAL,LAT,LON,ALT,VEL,BAT,SATS,FIX_OK,PKT_SEQ
  char buffer[160];
  mensajeRecibido.toCharArray(buffer, sizeof(buffer));

  char* devId = strtok(buffer, ",");
  char* animId = strtok(NULL, ",");
  char* latStr = strtok(NULL, ",");
  char* lonStr = strtok(NULL, ",");
  char* altStr = strtok(NULL, ",");
  char* velStr = strtok(NULL, ",");
  char* batStr = strtok(NULL, ",");
  char* satStr = strtok(NULL, ",");
  char* fixStr = strtok(NULL, ",");
  char* seqStr = strtok(NULL, ",");

  if (devId && animId && latStr && lonStr) {
    bool fixValido = (fixStr && strcmp(fixStr, "1") == 0);
    double latNum = atof(latStr);
    double lonNum = atof(lonStr);
    bool coordsValidas = (latNum >= -90.0 && latNum <= 90.0 &&
                          lonNum >= -180.0 && lonNum <= 180.0 &&
                          (latNum != 0.0 || lonNum != 0.0));

    const char* latPublicar = latStr;
    const char* lonPublicar = lonStr;

    if (fixValido && coordsValidas) {
      // Actualizar la memoria de posición válida del collar.
      strncpy(ultimaLatValida, latStr, sizeof(ultimaLatValida) - 1);
      ultimaLatValida[sizeof(ultimaLatValida) - 1] = '\0';
      strncpy(ultimaLonValida, lonStr, sizeof(ultimaLonValida) - 1);
      ultimaLonValida[sizeof(ultimaLonValida) - 1] = '\0';
      hayFixValido = true;
    } else {
      // Sin fix: reenviar la última coordenada válida, nunca un (0,0) falso.
      fixValido = false;
      if (hayFixValido) {
        latPublicar = ultimaLatValida;
        lonPublicar = ultimaLonValida;
      }
    }

    // Generar JSON conforme al contrato openspec/specs/contrato-mqtt/spec.md
    char jsonPayload[300];
    snprintf(jsonPayload, sizeof(jsonPayload),
      "{\"device_id\":\"%s\",\"animal_id\":\"%s\",\"lat\":%s,\"lon\":%s,\"altitud_m\":%s,"
      "\"velocidad_kmh\":%s,\"bateria_pct\":%s,\"rssi_dbm\":%d,\"snr_db\":%.1f,"
      "\"satelites\":%s,\"fix_valido\":%s}",
      devId, animId, latPublicar, lonPublicar,
      altStr ? altStr : "0.0",
      velStr ? velStr : "0.0",
      batStr ? batStr : "100",
      rssi, snr,
      satStr ? satStr : "0",
      fixValido ? "true" : "false"
    );

    // Publicar por MQTT
    char topic[64];
    snprintf(topic, sizeof(topic), "bovinos/%s/telemetria", devId);

    if (mqttClient.connected()) {
      mqttClient.publish(topic, jsonPayload);
      Serial.print("[MQTT TX] Publicado con éxito en ");
      Serial.println(topic);
    } else {
      Serial.println("[MQTT ERROR] No se pudo enviar por MQTT: cliente desconectado.");
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n[NODO 2 - GATEWAY] Inicializando...");

  // Inicializar radio LoRa
  SPI.begin(SCK_LORA, MISO_LORA, MOSI_LORA, SS_LORA);
  LoRa.setPins(SS_LORA, RST_LORA, DIO0_LORA);

  if (!LoRa.begin(BAND)) {
    Serial.println("[ERROR CRÍTICO] Fallo al iniciar LoRa en Gateway.");
    while (1);
  }

  LoRa.setTxPower(LORA_TX_POWER);   // 20 dBm (PA_BOOST) según firmware/AGENTS.md
  LoRa.setSpreadingFactor(LORA_SPREADING);
  LoRa.setSignalBandwidth(LORA_BW);
  LoRa.setSyncWord(0x34);
  Serial.println("[LoRa] Receptor activo en 915 MHz.");

  setupWiFi();
  mqttClient.setServer(MQTT_BROKER_HOST, MQTT_BROKER_PORT);
}

void loop() {
  // Mantener conexión Wi-Fi y MQTT
  if (WiFi.status() == WL_CONNECTED) {
    if (!mqttClient.connected()) {
      reconectarMQTT();
    }
    mqttClient.loop();
  }

  // Comprobar recepción LoRa de forma no bloqueante
  int packetSize = LoRa.parsePacket();
  if (packetSize) {
    procesarPaqueteLoRa(packetSize);
  }
}
