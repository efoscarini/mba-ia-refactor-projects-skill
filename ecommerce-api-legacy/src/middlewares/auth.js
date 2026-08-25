'use strict';

/**
 * Autorização em rota sensível (RF-15, resolve AP-11).
 *
 * O mecanismo é entregue por inteiro, mas a imposição fica atrás de
 * `AUTH_ENFORCED`, que nasce desligada — assim o contrato das rotas atuais
 * continua idêntico ao do código original. Com a flag desligada, cada acesso
 * anônimo a rota sensível vira log de aviso, para o buraco não ficar silencioso.
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
                    hint: 'AUTH_ENFORCED=false — defina como true para bloquear',
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
