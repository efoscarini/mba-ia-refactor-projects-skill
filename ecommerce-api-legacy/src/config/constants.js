'use strict';

/** Constantes de domínio — elimina os literais soltos do código original. */

const PAYMENT_STATUS = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED',
});

/** Bandeiras aceitas pelo gateway sandbox (antes: `cc.startsWith("4")` inline). */
const APPROVED_CARD_PREFIXES = Object.freeze(['4']);

const SCRYPT_KEY_LENGTH = 64;
const SCRYPT_SALT_BYTES = 16;
const GENERATED_PASSWORD_BYTES = 24;

const CARD_VISIBLE_DIGITS = 4;

module.exports = {
    PAYMENT_STATUS,
    APPROVED_CARD_PREFIXES,
    SCRYPT_KEY_LENGTH,
    SCRYPT_SALT_BYTES,
    GENERATED_PASSWORD_BYTES,
    CARD_VISIBLE_DIGITS,
};
