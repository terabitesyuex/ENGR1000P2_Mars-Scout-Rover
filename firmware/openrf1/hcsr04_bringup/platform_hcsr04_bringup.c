#include "platform_hcsr04_bringup.h"

#include "board_config.h"
#include "hcsr04.h"
#include "stm32f10x_gpio.h"
#include "stm32f10x_rcc.h"
#include "stm32f10x_tim.h"
#include "stm32f10x_usart.h"

static volatile uint32_t g_openrf1_hcsr04_millis = 0u;
static volatile uint8_t g_openrf1_hcsr04_platform_fault = 0u;

void SysTick_Handler(void) {
    ++g_openrf1_hcsr04_millis;
}

static void gpio_init(void) {
    GPIO_InitTypeDef gpio;
    RCC_APB2PeriphClockCmd(OPENRF1_HCSR04_TRIGGER_RCC | OPENRF1_HCSR04_ECHO_RCC, ENABLE);

    GPIO_StructInit(&gpio);
    gpio.GPIO_Pin = OPENRF1_HCSR04_TRIGGER_PIN;
    gpio.GPIO_Speed = GPIO_Speed_50MHz;
    gpio.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_Init(OPENRF1_HCSR04_TRIGGER_PORT, &gpio);
    GPIO_ResetBits(OPENRF1_HCSR04_TRIGGER_PORT, OPENRF1_HCSR04_TRIGGER_PIN);

    gpio.GPIO_Pin = OPENRF1_HCSR04_ECHO_PIN;
    gpio.GPIO_Mode = GPIO_Mode_IN_FLOATING;
    GPIO_Init(OPENRF1_HCSR04_ECHO_PORT, &gpio);
}

static void timer6_init(void) {
    TIM_TimeBaseInitTypeDef timer;
    RCC_APB1PeriphClockCmd(OPENRF1_HCSR04_TIMER_RCC, ENABLE);

    TIM_TimeBaseStructInit(&timer);
    timer.TIM_Period = OPENRF1_HCSR04_TIMER_PERIOD;
    timer.TIM_Prescaler = OPENRF1_HCSR04_TIMER_PRESCALER;
    timer.TIM_ClockDivision = TIM_CKD_DIV1;
    timer.TIM_CounterMode = TIM_CounterMode_Up;
    TIM_TimeBaseInit(OPENRF1_HCSR04_TIMER, &timer);
    TIM_SetCounter(OPENRF1_HCSR04_TIMER, 0u);
    TIM_Cmd(OPENRF1_HCSR04_TIMER, ENABLE);
}

static void debug_usart_init(void) {
    GPIO_InitTypeDef gpio;
    USART_InitTypeDef usart;

    RCC_APB2PeriphClockCmd(OPENRF1_HCSR04_DEBUG_GPIO_RCC | OPENRF1_HCSR04_DEBUG_USART_RCC, ENABLE);

    GPIO_StructInit(&gpio);
    gpio.GPIO_Pin = OPENRF1_HCSR04_DEBUG_TX_PIN;
    gpio.GPIO_Speed = GPIO_Speed_50MHz;
    gpio.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_Init(OPENRF1_HCSR04_DEBUG_TX_PORT, &gpio);

    gpio.GPIO_Pin = OPENRF1_HCSR04_DEBUG_RX_PIN;
    gpio.GPIO_Mode = GPIO_Mode_IN_FLOATING;
    GPIO_Init(OPENRF1_HCSR04_DEBUG_RX_PORT, &gpio);

    USART_StructInit(&usart);
    usart.USART_BaudRate = OPENRF1_HCSR04_DEBUG_BAUD;
    usart.USART_WordLength = USART_WordLength_8b;
    usart.USART_StopBits = USART_StopBits_1;
    usart.USART_Parity = USART_Parity_No;
    usart.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
    usart.USART_Mode = USART_Mode_Tx | USART_Mode_Rx;
    USART_Init(OPENRF1_HCSR04_DEBUG_USART, &usart);
    USART_Cmd(OPENRF1_HCSR04_DEBUG_USART, ENABLE);
}

OpenRf1Status openrf1_hcsr04_platform_init(void) {
    SystemCoreClockUpdate();
    if (SysTick_Config(SystemCoreClock / 1000u) != 0u) {
        g_openrf1_hcsr04_platform_fault = 1u;
        return OPENRF1_STATUS_HARDWARE_FAULT;
    }

    gpio_init();
    timer6_init();
    debug_usart_init();
    return OPENRF1_STATUS_OK;
}

uint32_t openrf1_hcsr04_millis(void) {
    return g_openrf1_hcsr04_millis;
}

uint32_t openrf1_hcsr04_timer_now_us(void) {
    return (uint32_t)TIM_GetCounter(OPENRF1_HCSR04_TIMER);
}

void openrf1_hcsr04_delay_us(uint16_t delay_us) {
    uint32_t start_us = openrf1_hcsr04_timer_now_us();
    uint32_t polls = 0u;
    while (hcsr04_elapsed_us(start_us, openrf1_hcsr04_timer_now_us(), OPENRF1_HCSR04_TIMER_MODULUS_US) < delay_us) {
        ++polls;
        if (polls >= OPENRF1_HCSR04_WAIT_POLL_LIMIT) {
            return;
        }
    }
}

void openrf1_hcsr04_trigger_write(uint8_t high) {
    if (high != 0u) {
        GPIO_SetBits(OPENRF1_HCSR04_TRIGGER_PORT, OPENRF1_HCSR04_TRIGGER_PIN);
    } else {
        GPIO_ResetBits(OPENRF1_HCSR04_TRIGGER_PORT, OPENRF1_HCSR04_TRIGGER_PIN);
    }
}

uint8_t openrf1_hcsr04_echo_read(void) {
    return GPIO_ReadInputDataBit(OPENRF1_HCSR04_ECHO_PORT, OPENRF1_HCSR04_ECHO_PIN) != 0u ? 1u : 0u;
}

void openrf1_hcsr04_debug_write_bounded(const char *text, uint16_t max_bytes) {
    if (text == 0 || g_openrf1_hcsr04_platform_fault != 0u) {
        return;
    }

    uint16_t sent = 0u;
    while (*text != '\0' && sent < max_bytes) {
        uint16_t spins = OPENRF1_HCSR04_DEBUG_TX_SPIN_LIMIT;
        while (USART_GetFlagStatus(OPENRF1_HCSR04_DEBUG_USART, USART_FLAG_TXE) == RESET && spins > 0u) {
            --spins;
        }
        if (spins == 0u) {
            return;
        }
        USART_SendData(OPENRF1_HCSR04_DEBUG_USART, (uint16_t)(uint8_t)*text);
        ++text;
        ++sent;
    }
}
