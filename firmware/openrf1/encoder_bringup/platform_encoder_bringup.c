#include "platform_encoder_bringup.h"

#include "board_config.h"
#include "stm32f10x.h"

static volatile uint32_t g_millis;
static volatile uint8_t g_tx_buffer[OPENRF1_ENCODER_BRINGUP_TX_BUFFER_BYTES];
static volatile uint16_t g_tx_head;
static volatile uint16_t g_tx_tail;

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

static void encoder_gpio_and_timers_init(void) {
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

    /* External 3.3 V pull-ups are required; inputs remain floating. */
    gpio_configure(GPIOA, 0u, 0x04u);
    gpio_configure(GPIOA, 1u, 0x04u);
    gpio_configure(GPIOA, 6u, 0x04u);
    gpio_configure(GPIOA, 7u, 0x04u);
    gpio_configure(GPIOA, 15u, 0x04u);
    gpio_configure(GPIOB, 3u, 0x04u);
    gpio_configure(GPIOB, 6u, 0x04u);
    gpio_configure(GPIOB, 7u, 0x04u);

    encoder_timer_configure(TIM5); /* CN1 */
    encoder_timer_configure(TIM3); /* CN2 */
    encoder_timer_configure(TIM2); /* CN3, full remap */
    encoder_timer_configure(TIM4); /* CN4 */
}

static void usart1_tx_init(void) {
    uint32_t divider;
    RCC->APB2ENR |= RCC_APB2ENR_IOPAEN | RCC_APB2ENR_USART1EN;
    gpio_configure(GPIOA, 9u, 0x0bu);
    divider = (SystemCoreClock + OPENRF1_ENCODER_BRINGUP_USART_BAUD / 2u) /
              OPENRF1_ENCODER_BRINGUP_USART_BAUD;
    USART1->CR1 = 0u;
    USART1->CR2 = 0u;
    USART1->CR3 = 0u;
    USART1->BRR = divider;
    USART1->CR1 = USART_CR1_UE | USART_CR1_TE;
    NVIC_ClearPendingIRQ(USART1_IRQn);
    NVIC_SetPriority(USART1_IRQn, 2u);
    NVIC_EnableIRQ(USART1_IRQn);
}

uint8_t openrf1_encoder_platform_init(void) {
    SystemCoreClockUpdate();
    g_millis = 0u;
    g_tx_head = 0u;
    g_tx_tail = 0u;
    encoder_gpio_and_timers_init();
    usart1_tx_init();
    return SysTick_Config(SystemCoreClock / 1000u) == 0u ? 1u : 0u;
}

uint32_t openrf1_encoder_millis(void) {
    return g_millis;
}

void openrf1_encoder_read_raw(uint16_t raw_counts[4]) {
    if (raw_counts == 0) {
        return;
    }
    raw_counts[0] = (uint16_t)TIM5->CNT;
    raw_counts[1] = (uint16_t)TIM3->CNT;
    raw_counts[2] = (uint16_t)TIM2->CNT;
    raw_counts[3] = (uint16_t)TIM4->CNT;
}

uint8_t openrf1_encoder_console_write(const char *text) {
    uint16_t length = 0u;
    uint16_t available;
    uint16_t index;
    uint32_t primask;
    if (text == 0) {
        return 0u;
    }
    while (text[length] != '\0' &&
           length < (uint16_t)(OPENRF1_ENCODER_BRINGUP_TX_BUFFER_BYTES - 1u)) {
        ++length;
    }
    if (text[length] != '\0') {
        return 0u;
    }
    primask = __get_PRIMASK();
    __disable_irq();
    available = g_tx_head >= g_tx_tail ?
        (uint16_t)(OPENRF1_ENCODER_BRINGUP_TX_BUFFER_BYTES -
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
            (g_tx_head + 1u) % OPENRF1_ENCODER_BRINGUP_TX_BUFFER_BYTES
        );
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

void USART1_IRQHandler(void) {
    uint32_t status = USART1->SR;
    if ((status & USART_SR_TXE) != 0u &&
        (USART1->CR1 & USART_CR1_TXEIE) != 0u) {
        if (g_tx_tail == g_tx_head) {
            USART1->CR1 &= ~USART_CR1_TXEIE;
        } else {
            USART1->DR = g_tx_buffer[g_tx_tail];
            g_tx_tail = (uint16_t)(
                (g_tx_tail + 1u) % OPENRF1_ENCODER_BRINGUP_TX_BUFFER_BYTES
            );
        }
    }
}
