'use strict';

/** Mapeamento HTTP -> controller de relatórios. Sem lógica. */

const express = require('express');
const { asyncHandler } = require('../middlewares/errorHandler');

function buildReportRoutes(controller) {
    const router = express.Router();
    router.get('/admin/financial-report', asyncHandler((req, res) => controller.financial(req, res)));
    return router;
}

module.exports = { buildReportRoutes };
