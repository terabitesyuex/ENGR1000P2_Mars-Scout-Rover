#include "platform_ground_sensors_bringup.h"

#include "board_config.h"
#include "stm32f10x_gpio.h"
#include "stm32f10x_rcc.h"
#include "stm32f10x_usart.h"

static volatile uint32_t g_openrf1_ground_millis = 0u;
static volatile uint8_t g_openrf1_ground_platform_fault = 0u;

void SysTick_Handler(void) {
    ++g_openrf1_ground_millis;
}

static void ground_gpio_init(void) {
    GPIO_InitTypeDef gpio;

    RCC_APB2PeriphClockCmd(
        OPENRF1_GROUND_LEFT_RCC | OPENRF1_GROUND_RIGHT_RCC | OPENRF1_GROUND_HALL_RCC,
        ENABLE
    );

    GPIO_StructInit(&gpio);
    gpio.GPIO_Pin = OPENRF1_GROUND_LEFT_PIN | OPENRF1_GROUND_RIGHT_PIN;
    gpio.GPIO_Speed = GPIO_Speed_50MHz;
    gpio.GPIO_Mode = GPIO_Mode_IN_FLOATING;
    GPIO_Init(OPENRF1_GROUND_LEFT_PORT, &gpio);

    gpio.GPIO_Pin = OPENRF1_GROUND_HALL_PIN;
    GPIO_Init(OPENRF1_GROUND_HALL_PORT, &gpio);
}

static void debug_usart_init(void) {
    GPIO_InitTypeDef gpio;
    USART_InitTypeDef usart;

    RCC_APB2PeriphClockCmd(OPENRF1_GROUND_DEBUG_GPIO_RCC | OPENRF1_GROUND_DEBUG_USART_RCC, ENABLE);

    GPIO_StructInit(&gpio);
    gpio.GPIO_Pin = OPENRF1_GROUND_DEBUG_TX_PIN;
    gpio.GPIO_Speed = GPIO_Speed_50MHz;
    gpio.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_Init(OPENRF1_GROUND_DEBUG_TX_PORT, &gpio);

    USART_StructInit(&usart);
    usart.USART_BaudRate = OPENRF1_GROUND_DEBUG_BAUD;
    usart.USART_WordLength = USART_WordLength_8b;
    usart.USART_StopBits = USART_StopBits_1;
    usart.USART_Parity = USART_Parity_No;
    usart.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
    usart.USART_Mode = USART_Mode_Tx;
    USART_Init(OPENRF1_GROUND_DEBUG_USART, &usart);
    USART_Cmd(OPENRF1_GROUND_DEBUG_USART, ENABLE);
}

OpenRf1Status openrf1_ground_platform_init(void) {
    SystemCoreClockUpdate();
    if (SysTick_Config(SystemCoreClock / 1000u) != 0u) {
        g_openrf1_ground_platform_fault = 1u;
        return OPENRF1_STATUS_HARDWARE_FAULT;
    }

    ground_gpio_init();
    debug_usart_init();
    return OPENRF1_STATUS_OK;
}

uint32_t openrf1_ground_millis(void) {
    return g_openrf1_ground_millis;
}

GroundSensorsRawLevels openrf1_ground_read_levels(void) {
    GroundSensorsRawLevels levels;
    levels.left_tcrt5000 = GPIO_ReadInputDataBit(OPENRF1_GROUND_LEFT_PORT, OPENRF1_GROUND_LEFT_PIN) != 0u ? 1u : 0u;
    levels.right_tcrt5000 = GPIO_ReadInputDataBit(OPENRF1_GROUND_RIGHT_PORT, OPENRF1_GROUND_RIGHT_PIN) != 0u ? 1u : 0u;
    levels.hall_sensor = GPIO_ReadInputDataBit(OPENRF1_GROUND_HALL_PORT, OPENRF1_GROUND_HALL_PIN) != 0u ? 1u : 0u;
    return levels;
}

void openrf1_ground_debug_write_bounded(const char *text, uint16_t max_bytes) {
    if (text == 0 || g_openrf1_ground_platform_fault != 0u) {
        return;
    }

    uint16_t sent = 0u;
    while (*text != '\0' && sent < max_bytes) {
        uint16_t spins = OPENRF1_GROUND_DEBUG_TX_SPIN_LIMIT;
        while (USART_GetFlagStatus(OPENRF1_GROUND_DEBUG_USART, USART_FLAG_TXE) == RESET && spins > 0u) {
            --spins;
        }
        if (spins == 0u) {
            return;
        }
        USART_SendData(OPENRF1_GROUND_DEBUG_USART, (uint16_t)(uint8_t)*text);
        ++text;
        ++sent;
    }
}
