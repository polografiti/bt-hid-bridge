#pragma once

// ─── Wi-Fi ────────────────────────────────────────────────────────────────────
#define WIFI_SSID           "YourSSID"
#define WIFI_PASSWORD       "YourPassword"
#define WIFI_RETRY_MAX      10

// ─── UDP Target (PC running receiver.py) ─────────────────────────────────────
#define PC_IP               "192.168.1.100"
#define UDP_PORT            9000

// ─── Test event loop (Milestone 1 only) ──────────────────────────────────────
// Interval in milliseconds between simulated event bursts
#define TEST_EVENT_INTERVAL_MS  150
