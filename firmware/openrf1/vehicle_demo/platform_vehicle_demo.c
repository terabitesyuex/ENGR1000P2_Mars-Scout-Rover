#include "platform_vehicle_demo.h"

#include "demo_config.h"
#include "stm32f10x.h"

typedef struct {
    GPIO_TypeDef *port;
    uint8_t pin;
} DemoGpioPin;

static const DemoGpioPin g_trigger_pins[3] = {
    {GPIOB, 9u}, {GPIOB, 5u}, {GPIOD, 2u}
};
static const DemoGpioPin g_echo_pins[3] = {
    {GPIOB, 8u}, {GPIOB, 4u}, {GPIOC, 11u}
};
static const DemoGpioPin g_hall_pin = {GPIOB, 0u};

static volatile uint32_t g_millis;
static volatile uint32_t g_timer6_overflows;
static volatile uint8_t g_rx_buffer[OPENRF1_DEMO_UART_RX_BUFFER_BYTES];
static volatile uint16_t g_rx_head;
static volatile uint16_t g_rx_tail;
static volatile uint8_t g_tx_buffer[OPENRF1_DEMO_UART_TX_BUFFER_BYTES];
static volatile uint16_t g_tx_head;
static volatile uint16_t g_tx_tail;
static volatile uint8_t g_console_fault;
static uint16_t g_line_length;

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

static void pin_write(const DemoGpioPin *pin, uint8_t high) {
    if (high != 0u) {
        pin->port->BSRR = (uint32_t)1u << pin->pin;
    } else {
        pin->port->BRR = (uint32_t)1u << pin->pin;
    }
}

static uint8_t pin_read(const DemoGpioPin *pin) {
    return (uint8_t)((pin->port->IDR & ((uint32_t)1u << pin->pin)) != 0u);
}

static void motor_direction_outputs_low(void) {
    GPIOA->BRR = GPIO_BRR_BR8 | GPIO_BRR_BR11 | GPIO_BRR_BR12;
    GPIOC->BRR = GPIO_BRR_BR10;
}

void demo_platform_stop_all(void) {
    TIM8->CCR1 = 0u;
    TIM8->CCR2 = 0u;
    TIM8->CCR3 = 0u;
    TIM8->CCR4 = 0u;
    motor_direction_outputs_low();
}

static void motor_init(void) {
    RCC->APB2ENR |= RCC_APB2ENR_AFIOEN |
                    RCC_APB2ENR_IOPAEN |
                    RCC_APB2ENR_IOPCEN |
                    RCC_APB2ENR_TIM8EN;

    motor_direction_outputs_low();
    gpio_configure(GPIOA, 8u, 0x03u);
    gpio_configure(GPIOA, 11u, 0x03u);
    gpio_configure(GPIOA, 12u, 0x03u);
    gpio_configure(GPIOC, 10u, 0x03u);
    motor_direction_outputs_low();

    /* Match the hardware team's validated TIM8 output idle initialization. */
    GPIOC->BRR = GPIO_BRR_BR6 | GPIO_BRR_BR7 | GPIO_BRR_BR8 | GPIO_BRR_BR9;
    gpio_configure(GPIOC, 6u, 0x0bu);
    gpio_configure(GPIOC, 7u, 0x0bu);
    gpio_configure(GPIOC, 8u, 0x0bu);
    gpio_configure(GPIOC, 9u, 0x0bu);

    TIM8->CR1 = 0u;
    TIM8->CCER = 0u;
    TIM8->PSC = OPENRF1_DEMO_PWM_PRESCALER;
    TIM8->ARR = OPENRF1_DEMO_PWM_AUTO_RELOAD;
    TIM8->CCR1 = 0u;
    TIM8->CCR2 = 0u;
    TIM8->CCR3 = 0u;
    TIM8->CCR4 = 0u;
    TIM8->CCMR1 = (6u << 4) | TIM_CCMR1_OC1PE |
                  (6u << 12) | TIM_CCMR1_OC2PE;
    TIM8->CCMR2 = (6u << 4) | TIM_CCMR2_OC3PE |
                  (6u << 12) | TIM_CCMR2_OC4PE;
    TIM8->CCER = TIM_CCER_CC1E | TIM_CCER_CC2E |
                 TIM_CCER_CC3E | TIM_CCER_CC4E;
    TIM8->CR1 = TIM_CR1_ARPE;
    TIM8->EGR = TIM_EGR_UG;
    TIM8->BDTR = TIM_BDTR_MOE;
    TIM8->CR1 |= TIM_CR1_CEN;
    demo_platform_stop_all();
}

static uint16_t connector_scale_permille(uint8_t connector) {
    switch (connector) {
        case 1u:
            return OPENRF1_DEMO_CN1_SPEED_SCALE_PERMILLE;
        case 2u:
            return OPENRF1_DEMO_CN2_SPEED_SCALE_PERMILLE;
        case 3u:
            return OPENRF1_DEMO_CN3_SPEED_SCALE_PERMILLE;
        case 4u:
            return OPENRF1_DEMO_CN4_SPEED_SCALE_PERMILLE;
        default:
            return 0u;
    }
}

static int8_t connector_forward_electrical_direction(uint8_t connector) {
    return connector == 1u || connector == 2u ? -1 : 1;
}

static void motor_set_raw_no_stop(
    uint8_t connector,
    uint16_t duty_permille,
    int8_t electrical_direction
) {
    uint32_t compare;
    uint32_t reverse_compare;

    if (connector < 1u || connector > 4u || duty_permille > 1000u) {
        return;
    }
    compare = ((uint32_t)(OPENRF1_DEMO_PWM_AUTO_RELOAD + 1u) * duty_permille) / 1000u;
    if (compare > OPENRF1_DEMO_PWM_AUTO_RELOAD) {
        compare = OPENRF1_DEMO_PWM_AUTO_RELOAD;
    }
    reverse_compare = OPENRF1_DEMO_PWM_AUTO_RELOAD - compare;

    if (connector == 1u) {
        if (electrical_direction >= 0) {
            GPIOA->BRR = GPIO_BRR_BR8;
            TIM8->CCR1 = compare;
        } else {
            GPIOA->BSRR = GPIO_BSRR_BS8;
            TIM8->CCR1 = reverse_compare;
        }
    } else if (connector == 2u) {
        if (electrical_direction >= 0) {
            GPIOA->BRR = GPIO_BRR_BR11;
            TIM8->CCR2 = compare;
        } else {
            GPIOA->BSRR = GPIO_BSRR_BS11;
            TIM8->CCR2 = reverse_compare;
        }
    } else if (connector == 3u) {
        if (electrical_direction >= 0) {
            GPIOA->BRR = GPIO_BRR_BR12;
            TIM8->CCR3 = compare;
        } else {
            GPIOA->BSRR = GPIO_BSRR_BS12;
            TIM8->CCR3 = reverse_compare;
        }
    } else {
        if (electrical_direction >= 0) {
            GPIOC->BRR = GPIO_BRR_BR10;
            TIM8->CCR4 = compare;
        } else {
            GPIOC->BSRR = GPIO_BSRR_BS10;
            TIM8->CCR4 = reverse_compare;
        }
    }
}

static void motor_set_physical_connector(
    uint8_t connector,
    int8_t physical_direction,
    uint16_t duty_permille
) {
    int8_t electrical_direction;
    uint16_t compensated_duty;
    if (physical_direction == 0) {
        return;
    }
    electrical_direction = (int8_t)(
        physical_direction * connector_forward_electrical_direction(connector)
    );
    compensated_duty = electrical_direction >= 0 ?
        OPENRF1_DEMO_ELECTRICAL_FORWARD_DUTY_PERMILLE :
        OPENRF1_DEMO_ELECTRICAL_REVERSE_DUTY_PERMILLE;
    if (compensated_duty > duty_permille && duty_permille < 500u) {
        compensated_duty = duty_permille;
    }
    compensated_duty = (uint16_t)(
        ((uint32_t)compensated_duty * connector_scale_permille(connector)) / 1000u
    );
    if (compensated_duty > 1000u) {
        compensated_duty = 1000u;
    }
    motor_set_raw_no_stop(connector, compensated_duty, electrical_direction);
}

static void motor_set_physical_motion(
    int8_t cn1_physical_direction,
    int8_t cn2_physical_direction,
    int8_t cn3_physical_direction,
    int8_t cn4_physical_direction,
    uint16_t duty_permille
) {
    if (duty_permille > 1000u) {
        demo_platform_stop_all();
        return;
    }

    demo_platform_stop_all();
    motor_set_physical_connector(1u, cn1_physical_direction, duty_permille);
    motor_set_physical_connector(2u, cn2_physical_direction, duty_permille);
    motor_set_physical_connector(3u, cn3_physical_direction, duty_permille);
    motor_set_physical_connector(4u, cn4_physical_direction, duty_permille);
}

void demo_platform_set_motion(DemoMotion motion) {
    if (motion == DEMO_MOTION_FORWARD) {
        motor_set_physical_motion(-1, -1, -1, -1, OPENRF1_DEMO_MOTION_DUTY_PERMILLE);
    } else if (motion == DEMO_MOTION_TURN_RIGHT) {
        motor_set_physical_motion(-1, -1, 1, 1, OPENRF1_DEMO_MOTION_DUTY_PERMILLE);
    } else if (motion == DEMO_MOTION_TURN_LEFT) {
        motor_set_physical_motion(1, 1, -1, -1, OPENRF1_DEMO_MOTION_DUTY_PERMILLE);
    } else {
        demo_platform_stop_all();
    }
}

void demo_platform_read_motor_diagnostics(DemoMotorDiagnostics *diagnostics) {
    if (diagnostics == 0) {
        return;
    }
    diagnostics->ccr1 = (uint16_t)TIM8->CCR1;
    diagnostics->ccr2 = (uint16_t)TIM8->CCR2;
    diagnostics->ccr3 = (uint16_t)TIM8->CCR3;
    diagnostics->ccr4 = (uint16_t)TIM8->CCR4;
    diagnostics->timer_cr1 = TIM8->CR1;
    diagnostics->timer_ccer = TIM8->CCER;
    diagnostics->timer_bdtr = TIM8->BDTR;
    diagnostics->gpio_c_crl = GPIOC->CRL;
    diagnostics->gpio_c_crh = GPIOC->CRH;
    diagnostics->afio_mapr = AFIO->MAPR;
}

static void ultrasonic_gpio_init(void) {
    uint8_t index;
    RCC->APB2ENR |= RCC_APB2ENR_IOPBEN | RCC_APB2ENR_IOPCEN | RCC_APB2ENR_IOPDEN;

    for (index = 0u; index < 3u; ++index) {
        gpio_configure(g_trigger_pins[index].port, g_trigger_pins[index].pin, 0x03u);
        pin_write(&g_trigger_pins[index], 0u);
        gpio_configure(g_echo_pins[index].port, g_echo_pins[index].pin, 0x08u);
        pin_write(&g_echo_pins[index], 0u);
    }
}

static void hall_gpio_init(void) {
    RCC->APB2ENR |= RCC_APB2ENR_IOPBEN;
    gpio_configure(g_hall_pin.port, g_hall_pin.pin, 0x04u);
}

static void encoder_timer_configure(TIM_TypeDef *timer) {
    timer->CR1 = 0u;
    timer->SMCR = 3u;
    timer->CCMR1 = 1u | (1u << 8);
    timer->CCER = 0u;
    timer->PSC = 0u;
    timer->ARR = UINT16_MAX;
    timer->CNT = 0u;
    timer->SR = 0u;
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

    /* External 3.3 V pull-ups are required; configure floating inputs only. */
    gpio_configure(GPIOA, 0u, 0x04u);
    gpio_configure(GPIOA, 1u, 0x04u);
    gpio_configure(GPIOA, 6u, 0x04u);
    gpio_configure(GPIOA, 7u, 0x04u);
    gpio_configure(GPIOA, 15u, 0x04u);
    gpio_configure(GPIOB, 3u, 0x04u);
    gpio_configure(GPIOB, 6u, 0x04u);
    gpio_configure(GPIOB, 7u, 0x04u);

    encoder_timer_configure(TIM5); /* CN1: PA0 / PA1. */
    encoder_timer_configure(TIM3); /* CN2: PA6 / PA7. */
    encoder_timer_configure(TIM2); /* CN3: PA15 / PB3, full remap. */
    encoder_timer_configure(TIM4); /* CN4: PB6 / PB7. */
}

void demo_platform_encoder_read_raw(uint16_t raw_counts[4]) {
    if (raw_counts == 0) {
        return;
    }
    raw_counts[0] = (uint16_t)TIM5->CNT;
    raw_counts[1] = (uint16_t)TIM3->CNT;
    raw_counts[2] = (uint16_t)TIM2->CNT;
    raw_counts[3] = (uint16_t)TIM4->CNT;
}

void demo_platform_trigger_write(uint8_t channel, uint8_t high) {
    if (channel < 3u) {
        pin_write(&g_trigger_pins[channel], high);
    }
}

uint8_t demo_platform_echo_read(uint8_t channel) {
    return channel < 3u ? pin_read(&g_echo_pins[channel]) : 0u;
}

uint8_t demo_platform_hall_read(void) {
    return pin_read(&g_hall_pin);
}

static uint8_t timer6_init(void) {
    uint32_t timer_clock_hz = SystemCoreClock;
    uint32_t prescaler;
    if (timer_clock_hz < OPENRF1_DEMO_TIMER_TICK_HZ ||
        timer_clock_hz % OPENRF1_DEMO_TIMER_TICK_HZ != 0u) {
        return 0u;
    }
    prescaler = timer_clock_hz / OPENRF1_DEMO_TIMER_TICK_HZ - 1u;
    if (prescaler > UINT16_MAX) {
        return 0u;
    }
    RCC->APB1ENR |= RCC_APB1ENR_TIM6EN;
    TIM6->CR1 = 0u;
    TIM6->PSC = (uint16_t)prescaler;
    TIM6->ARR = UINT16_MAX;
    TIM6->CNT = 0u;
    TIM6->SR = 0u;
    TIM6->DIER = TIM_DIER_UIE;
    g_timer6_overflows = 0u;
    NVIC_ClearPendingIRQ(TIM6_IRQn);
    NVIC_SetPriority(TIM6_IRQn, 1u);
    NVIC_EnableIRQ(TIM6_IRQn);
    TIM6->CR1 = TIM_CR1_CEN;
    return 1u;
}

uint32_t demo_platform_micros(void) {
    uint32_t high_before;
    uint32_t high_after;
    uint16_t low;
    do {
        high_before = g_timer6_overflows;
        low = (uint16_t)TIM6->CNT;
        high_after = g_timer6_overflows;
    } while (high_before != high_after);
    if ((TIM6->SR & TIM_SR_UIF) != 0u && low < 0x8000u) {
        high_after += 1u;
    }
    return (high_after << 16) | low;
}

static void usart1_init(void) {
    uint32_t divider;
    RCC->APB2ENR |= RCC_APB2ENR_IOPAEN | RCC_APB2ENR_USART1EN;
    gpio_configure(GPIOA, 9u, 0x0bu);
    gpio_configure(GPIOA, 10u, 0x04u);
    divider = (SystemCoreClock + OPENRF1_DEMO_USART_BAUD_RATE / 2u) /
              OPENRF1_DEMO_USART_BAUD_RATE;
    USART1->CR1 = 0u;
    USART1->CR2 = 0u;
    USART1->CR3 = 0u;
    USART1->BRR = divider;
    USART1->CR1 = USART_CR1_UE | USART_CR1_TE | USART_CR1_RE | USART_CR1_RXNEIE;
    NVIC_ClearPendingIRQ(USART1_IRQn);
    NVIC_SetPriority(USART1_IRQn, 2u);
    NVIC_EnableIRQ(USART1_IRQn);
}

uint8_t demo_platform_init(void) {
    SystemCoreClockUpdate();
    g_millis = 0u;
    g_rx_head = 0u;
    g_rx_tail = 0u;
    g_tx_head = 0u;
    g_tx_tail = 0u;
    g_console_fault = 0u;
    g_line_length = 0u;
    motor_init();
    ultrasonic_gpio_init();
    hall_gpio_init();
    encoder_init();
    usart1_init();
    if (timer6_init() == 0u || SysTick_Config(SystemCoreClock / 1000u) != 0u) {
        demo_platform_stop_all();
        return 0u;
    }
    return 1u;
}

uint32_t demo_platform_millis(void) {
    return g_millis;
}

DemoConsoleReadResult demo_platform_console_read_line(char *line, uint16_t line_bytes) {
    if (line == 0 || line_bytes < 2u) {
        return DEMO_CONSOLE_FAULT;
    }
    if (g_console_fault != 0u) {
        g_console_fault = 0u;
        g_line_length = 0u;
        return DEMO_CONSOLE_FAULT;
    }
    while (g_rx_tail != g_rx_head) {
        uint8_t byte = g_rx_buffer[g_rx_tail];
        g_rx_tail = (uint16_t)((g_rx_tail + 1u) % OPENRF1_DEMO_UART_RX_BUFFER_BYTES);
        if (byte == '\r' || byte == '\n') {
            if (g_line_length != 0u) {
                line[g_line_length] = '\0';
                g_line_length = 0u;
                return DEMO_CONSOLE_LINE_READY;
            }
            continue;
        }
        if (byte >= (uint8_t)'a' && byte <= (uint8_t)'z') {
            byte = (uint8_t)(byte - (uint8_t)'a' + (uint8_t)'A');
        }
        if (byte == (uint8_t)' ' || byte == (uint8_t)'\t') {
            continue;
        }
        if (byte < 0x20u || byte > 0x7eu ||
            g_line_length >= (uint16_t)(line_bytes - 1u)) {
            g_line_length = 0u;
            return DEMO_CONSOLE_FAULT;
        }
        line[g_line_length++] = (char)byte;
    }
    return DEMO_CONSOLE_NO_LINE;
}

uint8_t demo_platform_console_write(const char *text) {
    uint16_t length = 0u;
    uint16_t available;
    uint32_t primask;
    uint16_t index;
    if (text == 0) {
        return 0u;
    }
    while (text[length] != '\0' &&
           length < (uint16_t)(OPENRF1_DEMO_UART_TX_BUFFER_BYTES - 1u)) {
        ++length;
    }
    if (text[length] != '\0') {
        return 0u;
    }
    primask = __get_PRIMASK();
    __disable_irq();
    available = g_tx_head >= g_tx_tail ?
        (uint16_t)(OPENRF1_DEMO_UART_TX_BUFFER_BYTES - (g_tx_head - g_tx_tail) - 1u) :
        (uint16_t)(g_tx_tail - g_tx_head - 1u);
    if (length > available) {
        if (primask == 0u) {
            __enable_irq();
        }
        return 0u;
    }
    for (index = 0u; index < length; ++index) {
        g_tx_buffer[g_tx_head] = (uint8_t)text[index];
        g_tx_head = (uint16_t)((g_tx_head + 1u) % OPENRF1_DEMO_UART_TX_BUFFER_BYTES);
    }
    USART1->CR1 |= USART_CR1_TXEIE;
    if (primask == 0u) {
        __enable_irq();
    }
    return 1u;
}

void SysTick_Handler(void) {
    ++g_millis;
}

void TIM6_IRQHandler(void) {
    if ((TIM6->SR & TIM_SR_UIF) != 0u) {
        TIM6->SR &= ~TIM_SR_UIF;
        ++g_timer6_overflows;
    }
}

void USART1_IRQHandler(void) {
    uint32_t status = USART1->SR;
    if ((status & USART_SR_RXNE) != 0u) {
        uint8_t byte = (uint8_t)USART1->DR;
        uint16_t next = (uint16_t)((g_rx_head + 1u) % OPENRF1_DEMO_UART_RX_BUFFER_BYTES);
        if (next == g_rx_tail) {
            g_console_fault = 1u;
        } else {
            g_rx_buffer[g_rx_head] = byte;
            g_rx_head = next;
        }
        if ((status & (USART_SR_ORE | USART_SR_NE | USART_SR_FE | USART_SR_PE)) != 0u) {
            g_console_fault = 1u;
        }
    } else if ((status & (USART_SR_ORE | USART_SR_NE | USART_SR_FE | USART_SR_PE)) != 0u) {
        volatile uint32_t discarded = USART1->DR;
        (void)discarded;
        g_console_fault = 1u;
    }
    if ((status & USART_SR_TXE) != 0u && (USART1->CR1 & USART_CR1_TXEIE) != 0u) {
        if (g_tx_tail == g_tx_head) {
            USART1->CR1 &= ~USART_CR1_TXEIE;
        } else {
            USART1->DR = g_tx_buffer[g_tx_tail];
            g_tx_tail = (uint16_t)((g_tx_tail + 1u) % OPENRF1_DEMO_UART_TX_BUFFER_BYTES);
        }
    }
}
