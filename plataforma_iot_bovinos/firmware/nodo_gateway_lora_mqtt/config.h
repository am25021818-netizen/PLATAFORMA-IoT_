#ifndef GATEWAY_CONFIG_H
#define GATEWAY_CONFIG_H

// Identificación del Gateway
#define GATEWAY_ID          "HELTEC-GTW-01"

// Parámetros de Red Wi-Fi
#define WIFI_SSID           "MI_RED_WIFI"
#define WIFI_PASSWORD       "MI_PASSWORD"

// Parámetros de Broker MQTT
#define MQTT_BROKER_HOST    "192.168.1.100" // Cambiar a la IP de tu servidor o host.docker.internal
#define MQTT_BROKER_PORT    1883
#define MQTT_USER           ""
#define MQTT_PASS           ""
#define MQTT_TOPIC_TELE     "bovinos/%s/telemetria"
#define MQTT_TOPIC_LWT      "bovinos/" GATEWAY_ID "/estado"

// Parámetros LoRa 915 MHz (deben coincidir con el collar)
#define BAND                915E6
#define LORA_SPREADING      7
#define LORA_BW             125E3

#endif
