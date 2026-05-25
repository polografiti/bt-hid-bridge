#include <string.h>
#include "esp_log.h"
#include "lwip/sockets.h"
#include "lwip/netdb.h"
#include "udp_sender.h"
#include "../config.h"

static const char *TAG = "udp";

static int s_sock = -1;
static struct sockaddr_in s_dest_addr;

esp_err_t udp_sender_init(void)
{
    s_sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (s_sock < 0) {
        ESP_LOGE(TAG, "socket() failed: errno %d", errno);
        return ESP_FAIL;
    }

    memset(&s_dest_addr, 0, sizeof(s_dest_addr));
    s_dest_addr.sin_family      = AF_INET;
    s_dest_addr.sin_port        = htons(UDP_PORT);
    inet_aton(PC_IP, &s_dest_addr.sin_addr);

    ESP_LOGI(TAG, "UDP socket ready → %s:%d", PC_IP, UDP_PORT);
    return ESP_OK;
}

esp_err_t udp_sender_send(const char *json)
{
    if (s_sock < 0) return ESP_ERR_INVALID_STATE;

    int len = strlen(json);
    int sent = sendto(s_sock, json, len, 0,
                      (struct sockaddr *)&s_dest_addr, sizeof(s_dest_addr));
    if (sent < 0) {
        ESP_LOGE(TAG, "sendto failed: errno %d", errno);
        return ESP_FAIL;
    }
    ESP_LOGD(TAG, "Sent: %s", json);
    return ESP_OK;
}

void udp_sender_deinit(void)
{
    if (s_sock >= 0) {
        close(s_sock);
        s_sock = -1;
    }
}
