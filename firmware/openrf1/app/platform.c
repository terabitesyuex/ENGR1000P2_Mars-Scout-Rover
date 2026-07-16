#include "main.h"

#include "board_config.h"
#include "soft_i2c.h"
#include "stm32f10x_gpio.h"
#include "stm32f10x_rcc.h"
#include "stm32f10x_usart.h"

static volatile uint32_t g_openrf1_millis = 0u;

void SysTick_Handler(void) {
    ++g_openrf1_millis;
}

static void openrf1_usart1_init(void) {
    GPIO_InitTypeDef gpio;
    USART_InitTypeDef usart;

    RCC_APB2PeriphClockCmd(
        OPENRF1_TELEMETRY_USART_TX_RCC |
        OPENRF1_TELEMETRY_USART_RX_RCC |
        OPENRF1_TELEMETRY_USART_RCC,
        ENABLE
    );

    GPIO_StructInit(&gpio);
    gpio.GPIO_Pin = OPENRF1_TELEMETRY_USART_TX_PIN;
    gpio.GPIO_Speed = GPIO_Speed_50MHz;
    gpio.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_Init(OPENRF1_TELEMETRY_USART_TX_PORT, &gpio);

    gpio.GPIO_Pin = OPENRF1_TELEMETRY_USART_RX_PIN;
    gpio.GPIO_Mode = GPIO_Mode_IN_FLOATING;
    GPIO_Init(OPENRF1_TELEMETRY_USART_RX_PORT, &gpio);

    USART_StructInit(&usart);
    usart.USART_BaudRate = OPENRF1_TELEMETRY_BAUD;
    usart.USART_WordLength = USART_WordLength_8b;
    usart.USART_StopBits = USART_StopBits_1;
    usart.USART_Parity = USART_Parity_No;
    usart.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
    usart.USART_Mode = USART_Mode_Tx | USART_Mode_Rx;

    USART_Init(OPENRF1_TELEMETRY_USART, &usart);
    USART_Cmd(OPENRF1_TELEMETRY_USART, ENABLE);
}

void openrf1_platform_init(void) {
    SystemCoreClockUpdate();

    if (SysTick_Config(SystemCoreClock / 1000u) != 0u) {
        while (1) {
        }
    }

    openrf1_usart1_init();
    openrf1_soft_i2c_init();
}

uint32_t openrf1_millis(void) {
    return g_openrf1_millis;
}

void openrf1_usart1_write(const char *text) {
    if (text == 0) {
        return;
    }

    while (*text != '\0') {
        while (USART_GetFlagStatus(
                   OPENRF1_TELEMETRY_USART,
                   USART_FLAG_TXE
               ) == RESET) {
        }

        USART_SendData(
            OPENRF1_TELEMETRY_USART,
            (uint16_t)(uint8_t)*text
        );

        ++text;
    }

    while (USART_GetFlagStatus(
               OPENRF1_TELEMETRY_USART,
               USART_FLAG_TC
           ) == RESET) {
    }
}