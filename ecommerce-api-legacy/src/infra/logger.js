'use strict';

/**
 * Logger com níveis — substitui os `console.log` diretos.
 * Nunca receba aqui número de cartão, senha ou chave de gateway.
 */

const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };

function createLogger(level = 'info') {
    const threshold = LEVELS[level] ?? LEVELS.info;

    const emit = (name, stream) => (message, meta) => {
        if (LEVELS[name] > threshold) return;
        const line = `${new Date().toISOString()} ${name.toUpperCase().padEnd(5)} ${message}`;
        stream(meta === undefined ? line : `${line} ${JSON.stringify(meta)}`);
    };

    return {
        error: emit('error', console.error),
        warn: emit('warn', console.warn),
        info: emit('info', console.log),
        debug: emit('debug', console.log),
    };
}

module.exports = { createLogger };
