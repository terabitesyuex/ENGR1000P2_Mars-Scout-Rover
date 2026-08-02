#include "platform_motor_bringup.h"

#include "board_config.h"
#include "stm32f10x.h"

static volatile uint32_t g_millis;
static volatile uint8_t g_tx_buffer[OPENRF1_MOTOR_BRINGUP_TX_BUFFER_BYTES];
static volatile uint16_t g_tx_head;
static volatile uint16_t g_tx_tail;
static volatile uint8_t g_rx_buffer[OPENRF1_MOTOR_BRINGUP_RX_BUFFER_BYTES];
static volatile uint16_t g_rx_head;
static volatile uint16_t g_rx_tail;
static volatile uint8_t g_rx_fault;

static void gpio_configure(GPIO_TypeDef *gpio, uint8_t pin, uint32_t nibble) {
    volatile uint32_t *configuration;
    uint32_t shift;
    uint32_t value;
    if (pin < 8u) {
        configuration = &gpio->CRL;
        shift = (uint32_t)pin * 4u;
    } else {
        configuration = &gpio->CRH;
        shift = ((uint32_t)pin - 8u) * 4u;
    }
    value = *configuration;
    value &= ~((uint32_t)0x0fu << shift);
    value |= (nibble & 0x0fu) << shift;
    *configuration = value;
}

static void motor_direction_outputs_low(void) {
    GPIOA->BRR = GPIO_BRR_BR8 | GPIO_BRR_BR11 | GPIO_BRR_BR12;
    GPIOC->BRR = GPIO_BRR_BR10;
}

void openrf1_motor_stop_all(void) {
    TIM8->CCER = 0u;
    TIM8->BDTR = 0u;
    TIM8->CCR1 = 0u;
    TIM8->CCR2 = 0u;
    TIM8->CCR3 = 0u;
    TIM8->CCR4 = 0u;
    motor_direction_outputs_low();
}

static void motor_init_disabled(void) {
    RCC->APB2ENR |= RCC_APB2ENR_IOPAEN |
                    RCC_APB2ENR_IOPCEN |
                    RCC_APB2ENR_TIM8EN;
    motor_direction_outputs_low();
    gpio_configure(GPIOA, 8u, 0x03u);
    gpio_configure(GPIOA, 11u, 0x03u);
    gpio_configure(GPIOA, 12u, 0x03u);
    gpio_configure(GPIOC, 10u, 0x03u);
    motor_direction_outputs_low();
    GPIOC->BRR = GPIO_BRR_BR6 | GPIO_BRR_BR7 | GPIO_BRR_BR8 | GPIO_BRR_BR9;
    gpio_configure(GPIOC, 6u, 0x0bu);
    gpio_configure(GPIOC, 7u, 0x0bu);
    gpio_configure(GPIOC, 8u, 0x0bu);
    gpio_configure(GPIOC, 9u, 0x0bu);

    TIM8->CR1 = 0u;
    TIM8->CCER = 0u;
    TIM8->BDTR = 0u;
    TIM8->PSC = OPENRF1_MOTOR_BRINGUP_PWM_PRESCALER;
    TIM8->ARR = OPENRF1_MOTOR_BRINGUP_PWM_AUTO_RELOAD;
    TIM8->CCR1 = 0u;
    TIM8->CCR2 = 0u;
    TIM8->CCR3 = 0u;
    TIM8->CCR4 = 0u;
    TIM8->CCMR1 = (6u << 4) | TIM_CCMR1_OC1PE |
                  (6u << 12) | TIM_CCMR1_OC2PE;
    TIM8->CCMR2 = (6u << 4) | TIM_CCMR2_OC3PE |
                  (6u << 12) | TIM_CCMR2_OC4PE;
    TIM8->CR1 = TIM_CR1_ARPE;
    TIM8->EGR = TIM_EGR_UG;
    TIM8->CR1 |= TIM_CR1_CEN;
    openrf1_motor_stop_all();
}

uint8_t openrf1_motor_apply(
    uint8_t connector,
    int8_t electrical_direction,
    uint16_t duty_permille
) {
    uint32_t compare;
    uint32_t reverse_compare;
    uint32_t channel_enable;
    volatile uint16_t *capture_compare;

    openrf1_motor_stop_all();
    if (connector < 1u || connector > 4u ||
        (electrical_direction != -1 && electrical_direction != 1) ||
        duty_permille == 0u ||
        duty_permille > OPENRF1_MOTOR_BRINGUP_DUTY_REPRESENTATION_MAX) {
        return 0u;
    }
    compare = ((uint32_t)(OPENRF1_MOTOR_BRINGUP_PWM_AUTO_RELOAD + 1u) *
               duty_permille) / 1000u;
    if (compare > OPENRF1_MOTOR_BRINGUP_PWM_AUTO_RELOAD) {
        compare = OPENRF1_MOTOR_BRINGUP_PWM_AUTO_RELOAD;
    }
    reverse_compare = OPENRF1_MOTOR_BRINGUP_PWM_AUTO_RELOAD - compare;

    if (connector == 1u) {
        capture_compare = &TIM8->CCR1;
        channel_enable = TIM_CCER_CC1E;
        if (electrical_direction > 0) {
            GPIOA->BRR = GPIO_BRR_BR8;
        } else {
            GPIOA->BSRR = GPIO_BSRR_BS8;
        }
    } else if (connector == 2u) {
        capture_compare = &TIM8->CCR2;
        channel_enable = TIM_CCER_CC2E;
        if (electrical_direction > 0) {
            GPIOA->BRR = GPIO_BRR_BR11;
        } else {
            GPIOA->BSRR = GPIO_BSRR_BS11;
        }
    } else if (connector == 3u) {
        capture_compare = &TIM8->CCR3;
        channel_enable = TIM_CCER_CC3E;
        if (electrical_direction > 0) {
            GPIOA->BRR = GPIO_BRR_BR12;
        } else {
            GPIOA->BSRR = GPIO_BSRR_BS12;
        }
    } else {
        capture_compare = &TIM8->CCR4;
        channel_enable = TIM_CCER_CC4E;
        if (electrical_direction > 0) {
            GPIOC->BRR = GPIO_BRR_BR10;
        } else {
            GPIOC->BSRR = GPIO_BSRR_BS10;
        }
    }
    *capture_compare = (uint16_t)(
        electrical_direction > 0 ? compare : reverse_compare
    );
    TIM8->CCER = channel_enable;
    TIM8->BDTR = TIM_BDTR_MOE;
    return 1u;
}

static void encoder_timer_configure(TIM_TypeDef *timer) {
    timer->CR1 = 0u;
    timer->SMCR = 3u;
    timer->CCMR1 = 1u | (1u << 8);
    timer->CCER = 0u;
    timer->PSC = 0u;
    timer->ARR = UINT16_MAX;
    timer->CNT = 0u;
    timer->EGR = TIM_EGR_UG;
    timer->SR = 0u;
    timer->CR1 = TIM_CR1_CEN;
}

static void encoder_init(void) {
    const uint32_t tim2_remap_mask = (uint32_t)0x00000300u;
    const uint32_t tim2_full_remap = (uint32_t)0x00000300u;
    const uint32_t swj_config_mask = (uint32_t)0x07000000u;
    const uint32_t swj_jtag_disabled_swd_enabled = (uint32_t)0x02000000u;
    uint32_t mapr;
    RCC->APB2ENR |= RCC_APB2ENR_AFIOEN |
                    RCC_APB2ENR_IOPAEN |
                    RCC_APB2ENR_IOPBEN;
    RCC->APB1ENR |= RCC_APB1ENR_TIM2EN |
                    RCC_APB1ENR_TIM3EN |
                    RCC_APB1ENR_TIM4EN |
                    RCC_APB1ENR_TIM5EN;
    mapr = AFIO->MAPR;
    mapr &= ~(tim2_remap_mask | swj_config_mask);
    mapr |= tim2_full_remap | swj_jtag_disabled_swd_enabled;
    AFIO->MAPR = mapr;
    gpio_configure(GPIOA, 0u, 0x04u);
    gpio_configure(GPIOA, 1u, 0x04u);
    gpio_configure(GPIOA, 6u, 0x04u);
    gpio_configure(GPIOA, 7u, 0x04u);
    gpio_configure(GPIOA, 15u, 0x04u);
    gpio_configure(GPIOB, 3u, 0x04u);
    gpio_configure(GPIOB, 6u, 0x04u);
    gpio_configure(GPIOB, 7u, 0x04u);
    encoder_timer_configure(TIM5);
    encoder_timer_configure(TIM3);
    encoder_timer_configure(TIM2);
    encoder_timer_configure(TIM4);
}

void openrf1_motor_read_encoder_raw(uint16_t raw_counts[4]) {
    if (raw_counts == 0) {
        return;
    }
    raw_counts[0] = (uint16_t)TIM5->CNT;
    raw_counts[1] = (uint16_t)TIM3->CNT;
    raw_counts[2] = (uint16_t)TIM2->CNT;
    raw_counts[3] = (uint16_t)TIM4->CNT;
}

static void usart1_init(void) {
    uint32_t divider;
    RCC->APB2ENR |= RCC_APB2ENR_IOPAEN | RCC_APB2ENR_USART1EN;
    gpio_configure(GPIOA, 9u, 0x0bu);
    gpio_configure(GPIOA, 10u, 0x04u);
    divider = (SystemCoreClock + OPENRF1_MOTOR_BRINGUP_USART_BAUD / 2u) /
              OPENRF1_MOTOR_BRINGUP_USART_BAUD;
    USART1->CR1 = 0u;
    USART1->CR2 = 0u;
    USART1->CR3 = 0u;
    USART1->BRR = divider;
    USART1->CR1 = USART_CR1_UE | USART_CR1_TE | USART_CR1_RE |
                  USART_CR1_RXNEIE;
    NVIC_ClearPendingIRQ(USART1_IRQn);
    NVIC_SetPriority(USART1_IRQn, 2u);
    NVIC_EnableIRQ(USART1_IRQn);
}

uint8_t openrf1_motor_platform_init(void) {
    SystemCoreClockUpdate();
    g_millis = 0u;
    g_tx_head = 0u;
    g_tx_tail = 0u;
    g_rx_head = 0u;
    g_rx_tail = 0u;
    g_rx_fault = 0u;
    encoder_init();
    motor_init_disabled();
    usart1_init();
    if (SysTick_Config(SystemCoreClock / 1000u) != 0u) {
        openrf1_motor_stop_all();
        return 0u;
    }
    return 1u;
}

uint32_t openrf1_motor_millis(void) {
    return g_millis;
}

uint8_t openrf1_motor_console_write(const char *text) {
    uint16_t length = 0u;
    uint16_t available;
    uint16_t index;
    uint32_t primask;
    if (text == 0) {
        return 0u;
    }
    while (text[length] != '\0' &&
           length < (uint16_t)(OPENRF1_MOTOR_BRINGUP_TX_BUFFER_BYTES - 1u)) {
        ++length;
    }
    if (text[length] != '\0') {
        return 0u;
    }
    primask = __get_PRIMASK();
    __disable_irq();
    available = g_tx_head >= g_tx_tail ?
        (uint16_t)(OPENRF1_MOTOR_BRINGUP_TX_BUFFER_BYTES -
                   (g_tx_head - g_tx_tail) - 1u) :
        (uint16_t)(g_tx_tail - g_tx_head - 1u);
    if (length > available) {
        if (primask == 0u) {
            __enable_irq();
        }
        return 0u;
    }
    for (index = 0u; index < length; ++index) {
        g_tx_buffer[g_tx_head] = (uint8_t)text[index];
        g_tx_head = (uint16_t)(
            (g_tx_head + 1u) % OPENRF1_MOTOR_BRINGUP_TX_BUFFER_BYTES
        );
    }
    USART1->CR1 |= USART_CR1_TXEIE;
    if (primask == 0u) {
        __enable_irq();
    }
    return 1u;
}

MotorConsoleReadResult openrf1_motor_console_read_line(
    char *line,
    uint16_t line_bytes
) {
    static uint16_t length;
    uint8_t byte;
    if (line == 0 || line_bytes < 2u || g_rx_fault != 0u) {
        length = 0u;
        g_rx_fault = 0u;
        return MOTOR_CONSOLE_FAULT;
    }
    while (g_rx_tail != g_rx_head) {
        byte = g_rx_buffer[g_rx_tail];
        g_rx_tail = (uint16_t)(
            (g_rx_tail + 1u) % OPENRF1_MOTOR_BRINGUP_RX_BUFFER_BYTES
        );
        if (byte == '\r') {
            continue;
        }
        if (byte == '\n') {
            if (length == 0u) {
                continue;
            }
            line[length] = '\0';
            length = 0u;
            return MOTOR_CONSOLE_LINE_READY;
        }
        if (length >= (uint16_t)(line_bytes - 1u)) {
            length = 0u;
            return MOTOR_CONSOLE_FAULT;
        }
        line[length++] = (char)byte;
    }
    return MOTOR_CONSOLE_NO_LINE;
}

void SysTick_Handler(void) {
    ++g_millis;
}

void USART1_IRQHandler(void) {
    uint32_t status = USART1->SR;
    if ((status & (USART_SR_ORE | USART_SR_NE | USART_SR_FE | USART_SR_PE)) != 0u) {
        (void)USART1->DR;
        g_rx_fault = 1u;
    } else if ((status & USART_SR_RXNE) != 0u) {
        uint16_t next;
        uint8_t byte = (uint8_t)USART1->DR;
        next = (uint16_t)(
            (g_rx_head + 1u) % OPENRF1_MOTOR_BRINGUP_RX_BUFFER_BYTES
        );
        if (next == g_rx_tail) {
            g_rx_fault = 1u;
        } else {
            g_rx_buffer[g_rx_head] = byte;
            g_rx_head = next;
        }
    }
    if ((status & USART_SR_TXE) != 0u &&
        (USART1->CR1 & USART_CR1_TXEIE) != 0u) {
        if (g_tx_tail == g_tx_head) {
            USART1->CR1 &= ~USART_CR1_TXEIE;
        } else {
            USART1->DR = g_tx_buffer[g_tx_tail];
            g_tx_tail = (uint16_t)(
                (g_tx_tail + 1u) % OPENRF1_MOTOR_BRINGUP_TX_BUFFER_BYTES
            );
        }
    }
}
