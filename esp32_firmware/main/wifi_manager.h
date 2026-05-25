#pragma once

#include "esp_err.h"

/**
 * Initialize Wi-Fi in station mode and block until connected or max retries
 * exhausted. Returns ESP_OK on success.
 */
esp_err_t wifi_manager_init(void);

/** Returns true if Wi-Fi is currently connected. */
bool wifi_manager_is_connected(void);
