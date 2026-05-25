#pragma once

#include "esp_err.h"

/**
 * Open a UDP socket bound to the target PC_IP:UDP_PORT defined in config.h.
 * Must be called after Wi-Fi is connected.
 */
esp_err_t udp_sender_init(void);

/**
 * Send a null-terminated JSON string as a single UDP datagram.
 * Returns ESP_OK on success.
 */
esp_err_t udp_sender_send(const char *json);

/** Close the UDP socket. */
void udp_sender_deinit(void);
