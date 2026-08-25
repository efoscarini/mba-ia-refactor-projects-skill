'use strict';

/**
 * Autorização em rota sensível (RF-15, resolve AP-11).
 *
 * A imposição nasce **ligada**: rota sensível sem credencial responde 401. É uma
 * mudança intencional de contrato, declarada no relatório de auditoria.
 *
 * `AUTH_ENFORCED=false` é a válvula de escape para uma janela de migração —
 * restaura o contrato original e transforma cada acesso anônimo a rota sensível
 * em log de aviso, para o buraco ficar visível em vez de silencioso.
 */

const { UnauthorizedError } = require('./errors');

function extractBearer(header) {
    return String(header || '').replace(/^Bearer /i, '').trim();
}

function buildRequireAuth({ config, authService, logger }) {
    return function requireAuth(req, res, next) {
        const token = extractBearer(req.headers.authorization);

        if (!config.auth.enforced) {
            if (!token) {
                logger.warn('Rota sensível acessada sem credencial', {
                    method: req.method,
                    path: req.originalUrl,
                    hint: 'AUTH_ENFORCED=false — imposição desligada por configuração',
                });
            }
            return next();
        }

        if (!token) return next(new UnauthorizedError('Credencial ausente'));

        try {
            req.userId = authService.verify(token);
            return next();
        } catch (err) {
            return next(err);
        }
    };
}

module.exports = { buildRequireAuth };
