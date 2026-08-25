'use strict';

/**
 * Validação de entrada.
 *
 * O handler original só checava presença de 4 campos, direto no meio do fluxo.
 * Aqui a checagem fica isolada e nomeia os campos abreviados da API pública
 * (`usr`, `eml`, `pwd`, `c_id`) em nomes de domínio, sem mudar o contrato.
 */

const { ValidationError } = require('./errors');

function validateCheckout(body = {}) {
    const name = body.usr;
    const email = body.eml;
    const password = body.pwd;
    const courseId = body.c_id;
    const card = body.card;

    // Mesma condição do projeto original: `pwd` continua opcional.
    if (!name || !email || !courseId || !card) {
        throw new ValidationError('Bad Request');
    }

    return { name, email, password, courseId, card: String(card) };
}

function validateUserId(params = {}) {
    const userId = Number(params.id);
    if (!Number.isInteger(userId) || userId <= 0) {
        throw new ValidationError('Bad Request');
    }
    return userId;
}

/** Entrada do login (RF-15). Aceita `eml`/`pwd` do checkout e também email/password. */
function validateLogin(body = {}) {
    const email = body.eml || body.email;
    const password = body.pwd || body.password;
    if (!email || !password) {
        throw new ValidationError('Bad Request');
    }
    return { email, password };
}

module.exports = { validateCheckout, validateUserId, validateLogin };
