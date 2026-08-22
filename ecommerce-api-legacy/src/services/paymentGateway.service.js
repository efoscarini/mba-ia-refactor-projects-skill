'use strict';

/**
 * Integração com o gateway de pagamento.
 *
 * Isolar o gateway atrás de uma interface é o que permite trocar o sandbox por
 * um provedor real sem tocar em controller ou rota. A chave chega por injeção e
 * o número do cartão nunca é logado inteiro — o código original imprimia o PAN
 * completo junto com a chave `pk_live_` no stdout.
 */

const { PAYMENT_STATUS, APPROVED_CARD_PREFIXES, CARD_VISIBLE_DIGITS } = require('../config/constants');

function maskCard(card) {
    const digits = String(card);
    return `**** **** **** ${digits.slice(-CARD_VISIBLE_DIGITS)}`;
}

class PaymentGatewayService {
    constructor({ apiKey, logger }) {
        this._apiKey = apiKey;
        this._logger = logger;
    }

    /** Regra do sandbox, idêntica à original: cartão iniciado em 4 é aprovado. */
    charge({ card, amount }) {
        const approved = APPROVED_CARD_PREFIXES.some((prefix) => String(card).startsWith(prefix));
        const status = approved ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;

        this._logger.info('Cobrança processada no gateway', {
            card: maskCard(card),
            amount,
            status,
        });

        return { status, amount };
    }
}

module.exports = { PaymentGatewayService, maskCard };
