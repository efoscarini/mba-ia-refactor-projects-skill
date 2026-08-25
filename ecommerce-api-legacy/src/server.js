'use strict';

/**
 * Composition root: instancia infraestrutura, monta as dependências, registra
 * rotas e middlewares. É o único lugar do projeto que faz `new` de infra.
 */

const express = require('express');

const { config } = require('./config');
const { Database } = require('./infra/database');
const { createLogger } = require('./infra/logger');
const { createSchema, seed } = require('./infra/schema');

const { UserModel } = require('./models/user.model');
const { CourseModel } = require('./models/course.model');
const { EnrollmentModel } = require('./models/enrollment.model');
const { PaymentModel } = require('./models/payment.model');
const { AuditLogModel } = require('./models/auditLog.model');

const { PasswordService } = require('./services/password.service');
const { AuthService } = require('./services/auth.service');
const { PaymentGatewayService } = require('./services/paymentGateway.service');
const { CheckoutService } = require('./services/checkout.service');
const { ReportService } = require('./services/report.service');
const { UserService } = require('./services/user.service');

const { CheckoutController } = require('./controllers/checkout.controller');
const { ReportController } = require('./controllers/report.controller');
const { UserController } = require('./controllers/user.controller');

const { buildRoutes } = require('./routes');
const { buildErrorHandler, notFoundHandler } = require('./middlewares/errorHandler');
const { buildRequireAuth } = require('./middlewares/auth');

async function createApp(overrides = {}) {
    const settings = overrides.config || config;
    const logger = overrides.logger || createLogger(settings.logLevel);

    // --- infraestrutura ---
    const db = overrides.db || new Database(settings.databasePath);
    const passwordService = new PasswordService();

    await createSchema(db);
    if (settings.seedOnBoot) {
        await seed(db, {
            hashPassword: (pwd) => passwordService.hash(pwd),
            seedPassword: settings.seedUserPassword || passwordService.generate(),
        });
    }

    // --- models ---
    const userModel = new UserModel(db);
    const courseModel = new CourseModel(db);
    const enrollmentModel = new EnrollmentModel(db);
    const paymentModel = new PaymentModel(db);
    const auditLogModel = new AuditLogModel(db);

    // --- services ---
    const paymentGateway = new PaymentGatewayService({
        apiKey: settings.payment.gatewayKey,
        logger,
    });
    const checkoutService = new CheckoutService({
        db, courseModel, userModel, enrollmentModel, paymentModel,
        auditLogModel, paymentGateway, passwordService, logger,
    });
    const reportService = new ReportService({
        courseModel, enrollmentModel, paymentModel, userModel,
    });
    const authService = new AuthService({
        secret: settings.auth.secret,
        tokenTtlSeconds: settings.auth.tokenTtlSeconds,
    });
    const userService = new UserService({
        db, userModel, auditLogModel, passwordService, authService, logger,
    });

    // --- controllers ---
    const checkoutController = new CheckoutController(checkoutService);
    const reportController = new ReportController(reportService);
    const userController = new UserController(userService);

    // --- aplicação ---
    const app = express();
    app.use(express.json());
    const requireAuth = buildRequireAuth({ config: settings, authService, logger });

    app.use('/api', buildRoutes({
        checkoutController, reportController, userController, requireAuth,
    }));
    app.use(notFoundHandler);
    app.use(buildErrorHandler(logger));

    return { app, db, logger, settings };
}

module.exports = { createApp };
