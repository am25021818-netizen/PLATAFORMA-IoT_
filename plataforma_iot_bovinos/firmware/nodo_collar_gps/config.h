#ifndef CONFIG_H
#define CONFIG_H

// Identificación del Dispositivo
#define DEVICE_ID       "HELTEC-COLLAR-01"
#define ANIMAL_ID       "BOV-001"

// Frecuencia LoRa (México / US915)
#define BAND            915E6
#define LORA_SPREADING  7
#define LORA_BW         125E3
#define LORA_TX_POWER   20

// Pines GPS para Heltec LoRa ESP32 v2
#define GPS_RX_PIN      22
#define GPS_TX_PIN      23
#define GPS_BAUD_RATE   9600

// Intervalo de transmisión (en milisegundos)
// 30000 ms para pruebas de laboratorio; 300000 ms (5 min) para campo
#define INTERVALO_ENVIO_MS  30000 

// Pin de medición de batería (divisor resistivo interno en Heltec v2: GPIO 37 o 36)
#define PIN_BATERIA         37

#endif
