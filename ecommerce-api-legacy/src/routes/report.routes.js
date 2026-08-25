'use strict';

/** Mapeamento HTTP -> controller de relatórios. Sem lógica. */

const express = require('express');
const { asyncHandler } = require('../middlewares/errorHandler');

function buildReportRoutes(controller, requireAuth) {
    const router = express.Router();
    // Sensível: agrega faturamento e expõe nome de todos os alunos pagantes.
    router.get(
        '/admin/financial-report',
        requireAuth,
        asyncHandler((req, res) => controller.financial(req, res)),
    );
    return router;
}

module.exports = { buildReportRoutes };
