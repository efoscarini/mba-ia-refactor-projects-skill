'use strict';

/**
 * Configuração da aplicação — lida exclusivamente de variáveis de ambiente.
 * Nenhum segredo é literal aqui (o `utils.js` original guardava senha de banco,
 * chave de gateway e usuário SMTP no código).
 */

const crypto = require('crypto');

const { DEFAULT_TOKEN_TTL_SECONDS } = require('./constants');

function asBool(raw, fallback = false) {
    if (raw === undefined || raw === null || raw === '') return fallback;
    return ['1', 'true', 'yes', 'on'].includes(String(raw).trim().toLowerCase());
}

function required(name, value, isProduction) {
    if (value) return value;
    if (isProduction) {
        throw new Error(`${name} não definida. Configure a variável de ambiente (veja .env.example).`);
    }
    return '';
}

const env = process.env;
const appEnv = env.APP_ENV || 'development';
const isProduction = ['production', 'prod'].includes(appEnv.toLowerCase());

const config = {
    appEnv,
    isProduction,
    port: Number(env.PORT || 3000),
    logLevel: env.LOG_LEVEL || 'info',
    databasePath: env.DATABASE_PATH || ':memory:',
    seedOnBoot: asBool(env.SEED_ON_BOOT, true),
    seedUserPassword: env.SEED_USER_PASSWORD || '',
    payment: {
        gatewayKey: required('PAYMENT_GATEWAY_KEY', env.PAYMENT_GATEWAY_KEY, isProduction),
    },
    smtp: {
        user: env.SMTP_USER || '',
        password: required('SMTP_PASSWORD', env.SMTP_PASSWORD, isProduction),
    },
    auth: {
        // RF-15: o mecanismo de autorização é sempre montado; só a imposição é
        // opcional. Desligada por padrão para preservar o contrato das rotas.
        enforced: asBool(env.AUTH_ENFORCED, false),
        secret: env.AUTH_SECRET || required('AUTH_SECRET', env.AUTH_SECRET, isProduction)
            || crypto.randomBytes(32).toString('hex'),
        tokenTtlSeconds: Number(env.AUTH_TOKEN_TTL || DEFAULT_TOKEN_TTL_SECONDS),
    },
};

module.exports = { config };
