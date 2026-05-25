/**
 * bt-hid-bridge — Milestone 1
 *
 * Connects to Wi-Fi and sends simulated HID events over UDP to the PC
 * receiver. No Bluetooth yet — this validates the full Wi-Fi→UDP→Python
 * pipeline before adding BT HID Host in Milestone 2.
 *
 * Test sequence (repeating):
 *   1. Type "hello " (key down/up for each character)
 *   2. Move mouse diagonally (+20, +10)
 *   3. Left-click
 *   4. Scroll down one notch
 *   5. Pause 500 ms then repeat
 */

#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "wifi_manager.h"
#include "udp_sender.h"
#include "../config.h"

static const char *TAG = "main";

// ─── Helpers ──────────────────────────────────────────────────────────────────

static void send_key(const char *key, const char *state)
{
    char buf[128];
    snprintf(buf, sizeof(buf),
             "{\"type\":\"key\",\"key\":\"%s\",\"state\":\"%s\"}", key, state);
    udp_sender_send(buf);
    vTaskDelay(pdMS_TO_TICKS(8));   // ~8 ms between down and up feels natural
}

static void send_char(char c)
{
    char key[4] = { c, 0 };
    send_key(key, "down");
    send_key(key, "up");
}

static void send_mouse_move(int dx, int dy)
{
    char buf[128];
    snprintf(buf, sizeof(buf),
             "{\"type\":\"mouse\",\"dx\":%d,\"dy\":%d}", dx, dy);
    udp_sender_send(buf);
}

static void send_mouse_button(const char *button, const char *state)
{
    char buf[128];
    snprintf(buf, sizeof(buf),
             "{\"type\":\"mouse_button\",\"button\":\"%s\",\"state\":\"%s\"}",
             button, state);
    udp_sender_send(buf);
    vTaskDelay(pdMS_TO_TICKS(8));
}

static void send_scroll(int dy)
{
    char buf[64];
    snprintf(buf, sizeof(buf), "{\"type\":\"scroll\",\"dy\":%d}", dy);
    udp_sender_send(buf);
}

// ─── Test event task ──────────────────────────────────────────────────────────

static void test_event_task(void *pvParam)
{
    // Wait for UDP socket to be ready (caller ensures this)
    ESP_LOGI(TAG, "Test event loop started — sending simulated HID events");

    const char *demo_str = "hello ";
    uint32_t cycle = 0;

    while (1) {
        ESP_LOGI(TAG, "── Cycle %lu ──", (unsigned long)cycle++);

        // Type "hello "
        for (int i = 0; demo_str[i]; i++) {
            send_char(demo_str[i]);
            vTaskDelay(pdMS_TO_TICKS(TEST_EVENT_INTERVAL_MS));
        }

        // Move mouse +20 right, +10 down (in small steps so it looks smooth)
        for (int i = 0; i < 4; i++) {
            send_mouse_move(5, 2);
            vTaskDelay(pdMS_TO_TICKS(16));
        }

        // Left click
        send_mouse_button("left", "down");
        send_mouse_button("left", "up");
        vTaskDelay(pdMS_TO_TICKS(50));

        // Scroll down
        send_scroll(-1);
        vTaskDelay(pdMS_TO_TICKS(50));

        // Brief pause before next cycle
        vTaskDelay(pdMS_TO_TICKS(800));
    }
}

// ─── Entry point ─────────────────────────────────────────────────────────────

void app_main(void)
{
    ESP_LOGI(TAG, "bt-hid-bridge Milestone 1 starting");

    if (wifi_manager_init() != ESP_OK) {
        ESP_LOGE(TAG, "Wi-Fi failed — halting");
        return;
    }

    if (udp_sender_init() != ESP_OK) {
        ESP_LOGE(TAG, "UDP init failed — halting");
        return;
    }

    xTaskCreate(test_event_task, "test_events", 4096, NULL, 5, NULL);
}
