'use strict';

/**
 * Emissão e verificação de token assinado (RF-15).
 *
 * O projeto não tem biblioteca de JWT e não vamos adicionar dependência: o
 * formato aqui é `base64url(payload).base64url(HMAC-SHA256(payload))`, assinado
 * com a chave do ambiente e comparado com `timingSafeEqual`.
 *
 * Isto NÃO é o `badCrypto()` de volta: assinatura é HMAC com chave secreta, um
 * primitivo padrão — o que o código original fazia era inventar um hash.
 */

const crypto = require('crypto');
const { UnauthorizedError } = require('../middlewares/errors');

function b64url(buffer) {
    return Buffer.from(buffer).toString('base64url');
}

class AuthService {
    constructor({ secret, tokenTtlSeconds }) {
        this.secret = secret;
        this.ttl = tokenTtlSeconds;
    }

    _sign(payloadB64) {
        return b64url(crypto.createHmac('sha256', this.secret).update(payloadB64).digest());
    }

    issue(userId) {
        const payload = { userId, exp: Math.floor(Date.now() / 1000) + this.ttl };
        const payloadB64 = b64url(JSON.stringify(payload));
        return `${payloadB64}.${this._sign(payloadB64)}`;
    }

    verify(token) {
        const [payloadB64, signature] = String(token).split('.');
        if (!payloadB64 || !signature) throw new UnauthorizedError('Token malformado');

        const expected = Buffer.from(this._sign(payloadB64));
        const received = Buffer.from(signature);
        if (expected.length !== received.length || !crypto.timingSafeEqual(expected, received)) {
            throw new UnauthorizedError('Assinatura inválida');
        }

        let payload;
        try {
            payload = JSON.parse(Buffer.from(payloadB64, 'base64url').toString());
        } catch {
            throw new UnauthorizedError('Token malformado');
        }
        if (payload.exp < Math.floor(Date.now() / 1000)) {
            throw new UnauthorizedError('Token expirado');
        }
        return payload.userId;
    }
}

module.exports = { AuthService };
