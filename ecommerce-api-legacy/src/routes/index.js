'use strict';

/** Agrega os routers sob o prefixo /api, preservando os paths originais. */

const express = require('express');
const { buildCheckoutRoutes } = require('./checkout.routes');
const { buildReportRoutes } = require('./report.routes');
const { buildUserRoutes } = require('./user.routes');

function buildRoutes({ checkoutController, reportController, userController, requireAuth }) {
    const router = express.Router();
    router.use(buildCheckoutRoutes(checkoutController));
    router.use(buildReportRoutes(reportController, requireAuth));
    router.use(buildUserRoutes(userController, requireAuth));
    return router;
}

module.exports = { buildRoutes };
