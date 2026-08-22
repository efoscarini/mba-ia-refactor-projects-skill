'use strict';

/** Agrega os routers sob o prefixo /api, preservando os paths originais. */

const express = require('express');
const { buildCheckoutRoutes } = require('./checkout.routes');
const { buildReportRoutes } = require('./report.routes');
const { buildUserRoutes } = require('./user.routes');

function buildRoutes({ checkoutController, reportController, userController }) {
    const router = express.Router();
    router.use(buildCheckoutRoutes(checkoutController));
    router.use(buildReportRoutes(reportController));
    router.use(buildUserRoutes(userController));
    return router;
}

module.exports = { buildRoutes };
