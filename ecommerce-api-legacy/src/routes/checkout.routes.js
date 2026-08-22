'use strict';

/** Mapeamento HTTP -> controller de checkout. Sem lógica. */

const express = require('express');
const { asyncHandler } = require('../middlewares/errorHandler');

function buildCheckoutRoutes(controller) {
    const router = express.Router();
    router.post('/checkout', asyncHandler((req, res) => controller.create(req, res)));
    return router;
}

module.exports = { buildCheckoutRoutes };
