'use strict';

/**
 * Caso de uso de checkout.
 *
 * Substitui os 5 níveis de callback aninhados do `AppManager.setupRoutes`:
 * o fluxo virou linear com `async/await` e as três escritas relacionadas
 * (matrícula, pagamento e auditoria) acontecem dentro de uma transação.
 */

const { PAYMENT_STATUS } = require('../config/constants');
const { NotFoundError, BusinessError } = require('../middlewares/errors');

class CheckoutService {
    constructor({
        db,
        courseModel,
        userModel,
        enrollmentModel,
        paymentModel,
        auditLogModel,
        paymentGateway,
        passwordService,
        logger,
    }) {
        this.db = db;
        this.courses = courseModel;
        this.users = userModel;
        this.enrollments = enrollmentModel;
        this.payments = paymentModel;
        this.auditLogs = auditLogModel;
        this.gateway = paymentGateway;
        this.passwords = passwordService;
        this.logger = logger;
    }

    async execute({ name, email, password, courseId, card }) {
        const course = await this.courses.findActiveById(courseId);
        if (!course) {
            throw new NotFoundError('Curso não encontrado');
        }

        const user = await this._findOrCreateUser({ name, email, password });

        const payment = this.gateway.charge({ card, amount: course.price });
        if (payment.status === PAYMENT_STATUS.DENIED) {
            throw new BusinessError('Pagamento recusado');
        }

        const enrollmentId = await this.db.transaction(async (tx) => {
            const id = await this.enrollments.create({ userId: user.id, courseId }, tx);
            await this.payments.create(
                { enrollmentId: id, amount: course.price, status: payment.status },
                tx,
            );
            await this.auditLogs.record(`Checkout curso ${courseId} por ${user.id}`, tx);
            return id;
        });

        this.logger.info('Checkout concluído', {
            userId: user.id,
            courseId,
            enrollmentId,
        });

        return { enrollmentId };
    }

    async _findOrCreateUser({ name, email, password }) {
        const existing = await this.users.findByEmail(email);
        if (existing) return existing;

        // `pwd` é opcional no contrato; sem ele, gera-se uma senha aleatória.
        const plainPassword = password || this.passwords.generate();
        return this.users.create({
            name,
            email,
            passwordHash: await this.passwords.hash(plainPassword),
        });
    }
}

module.exports = { CheckoutService };
