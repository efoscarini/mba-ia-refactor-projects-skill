'use strict';

/**
 * Tratamento de erro centralizado.
 *
 * No projeto original cada callback tratava (ou ignorava) o próprio erro, e
 * vários `if (err)` simplesmente não existiam — a requisição ficava pendurada.
 * Aqui todo erro assíncrono chega em um lugar só.
 */

const { AppError } = require('./errors');

/** Envolve um handler async para que rejeições cheguem ao error handler. */
function asyncHandler(fn) {
    return (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
}

function notFoundHandler(req, res) {
    res.status(404).send('Recurso não encontrado');
}

function buildErrorHandler(logger) {
    // A assinatura de 4 argumentos é o que marca o middleware como error handler.
    return (err, req, res, _next) => {
        if (err instanceof AppError) {
            logger.info(`Erro de domínio (${err.status}): ${err.message}`);
            return res.status(err.status).send(err.message);
        }
        // stack trace vai para o log; o cliente recebe apenas a mensagem genérica
        logger.error(`Erro não tratado em ${req.method} ${req.originalUrl}`, {
            message: err.message,
            stack: err.stack,
        });
        return res.status(500).send('Erro Interno');
    };
}

module.exports = { asyncHandler, notFoundHandler, buildErrorHandler };
