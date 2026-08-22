'use strict';

/** Mapeamento HTTP -> controller de usuários. Sem lógica. */

const express = require('express');
const { asyncHandler } = require('../middlewares/errorHandler');

function buildUserRoutes(controller) {
    const router = express.Router();
    router.delete('/users/:id', asyncHandler((req, res) => controller.remove(req, res)));
    return router;
}

module.exports = { buildUserRoutes };
