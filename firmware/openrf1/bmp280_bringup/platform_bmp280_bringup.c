#include "platform_bmp280_bringup.h"

#include "board_config.h"
#include "stm32f10x_gpio.h"
#include "stm32f10x_rcc.h"
#include "stm32f10x_usart.h"

static volatile uint32_t g_openrf1_bmp280_millis = 0u;
static volatile uint8_t g_openrf1_bmp280_systick_fault = 0u;

void SysTick_Handler(void) {
    ++g_openrf1_bmp280_millis;
}

static void debug_usart_init(void) {
    GPIO_InitTypeDef gpio;
    USART_InitTypeDef usart;

    RCC_APB2PeriphClockCmd(OPENRF1_BMP280_DEBUG_GPIO_RCC | OPENRF1_BMP280_DEBUG_USART_RCC, ENABLE);

    GPIO_StructInit(&gpio);
    gpio.GPIO_Pin = OPENRF1_BMP280_DEBUG_TX_PIN;
    gpio.GPIO_Speed = GPIO_Speed_50MHz;
    gpio.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_Init(OPENRF1_BMP280_DEBUG_TX_PORT, &gpio);

    gpio.GPIO_Pin = OPENRF1_BMP280_DEBUG_RX_PIN;
    gpio.GPIO_Mode = GPIO_Mode_IN_FLOATING;
    GPIO_Init(OPENRF1_BMP280_DEBUG_RX_PORT, &gpio);

    USART_StructInit(&usart);
    usart.USART_BaudRate = OPENRF1_BMP280_DEBUG_BAUD;
    usart.USART_WordLength = USART_WordLength_8b;
    usart.USART_StopBits = USART_StopBits_1;
    usart.USART_Parity = USART_Parity_No;
    usart.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
    usart.USART_Mode = USART_Mode_Tx | USART_Mode_Rx;
    USART_Init(OPENRF1_BMP280_DEBUG_USART, &usart);
    USART_Cmd(OPENRF1_BMP280_DEBUG_USART, ENABLE);
}

void openrf1_bmp280_platform_init(void) {
    SystemCoreClockUpdate();
    if (SysTick_Config(SystemCoreClock / 1000u) != 0u) {
        g_openrf1_bmp280_systick_fault = 1u;
    }
    debug_usart_init();
}

uint32_t openrf1_bmp280_millis(void) {
    return g_openrf1_bmp280_millis;
}

void openrf1_bmp280_debug_write_bounded(const char *text, uint16_t max_bytes) {
    if (text == 0 || g_openrf1_bmp280_systick_fault != 0u) {
        return;
    }

    uint16_t sent = 0u;
    while (*text != '\0' && sent < max_bytes) {
        uint16_t spins = OPENRF1_BMP280_DEBUG_TX_SPIN_LIMIT;
        while (USART_GetFlagStatus(OPENRF1_BMP280_DEBUG_USART, USART_FLAG_TXE) == RESET && spins > 0u) {
            --spins;
        }
        if (spins == 0u) {
            return;
        }
        USART_SendData(OPENRF1_BMP280_DEBUG_USART, (uint16_t)(uint8_t)*text);
        ++text;
        ++sent;
    }
}
