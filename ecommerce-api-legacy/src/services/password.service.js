'use strict';

/**
 * Hash de senha com `crypto.scrypt` (salt aleatório, KDF lento).
 *
 * Substitui o `badCrypto()` do `utils.js`: um laço de 10.000 concatenações de
 * base64 truncado em 10 caracteres, sem salt — reversível e com colisão trivial.
 */

const crypto = require('crypto');
const {
    SCRYPT_KEY_LENGTH,
    SCRYPT_SALT_BYTES,
    GENERATED_PASSWORD_BYTES,
} = require('../config/constants');

function scrypt(password, salt) {
    return new Promise((resolve, reject) => {
        crypto.scrypt(password, salt, SCRYPT_KEY_LENGTH, (err, derived) =>
            (err ? reject(err) : resolve(derived)));
    });
}

class PasswordService {
    async hash(plainPassword) {
        const salt = crypto.randomBytes(SCRYPT_SALT_BYTES).toString('hex');
        const derived = await scrypt(plainPassword, salt);
        return `scrypt$${salt}$${derived.toString('hex')}`;
    }

    async verify(plainPassword, stored) {
        const [algorithm, salt, hash] = String(stored).split('$');
        if (algorithm !== 'scrypt' || !salt || !hash) return false;
        const derived = await scrypt(plainPassword, salt);
        const expected = Buffer.from(hash, 'hex');
        return derived.length === expected.length && crypto.timingSafeEqual(derived, expected);
    }

    /**
     * O checkout aceita requisição sem `pwd`. O código original caía num
     * literal fixo ("123456"); aqui a senha provisória é aleatória.
     */
    generate() {
        return crypto.randomBytes(GENERATED_PASSWORD_BYTES).toString('base64url');
    }
}

module.exports = { PasswordService };
