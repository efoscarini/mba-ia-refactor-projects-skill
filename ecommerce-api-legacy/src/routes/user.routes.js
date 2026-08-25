'use strict';

/** Mapeamento HTTP -> controller de usuários. Sem lógica. */

const express = require('express');
const { asyncHandler } = require('../middlewares/errorHandler');

function buildUserRoutes(controller, requireAuth) {
    const router = express.Router();
    // Aditiva (RF-15): emite a credencial que o middleware verifica.
    router.post('/login', asyncHandler((req, res) => controller.login(req, res)));
    // Sensível: apaga registro de terceiro, em cascata.
    router.delete('/users/:id', requireAuth, asyncHandler((req, res) => controller.remove(req, res)));
    return router;
}

module.exports = { buildUserRoutes };
