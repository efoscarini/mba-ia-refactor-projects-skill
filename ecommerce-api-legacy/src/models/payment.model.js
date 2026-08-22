'use strict';

/** Acesso a dados de pagamentos. */

class PaymentModel {
    constructor(db) {
        this.db = db;
    }

    async create({ enrollmentId, amount, status }, executor = this.db) {
        const result = await executor.run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amount, status],
        );
        return result.lastID;
    }

    listAll() {
        return this.db.all('SELECT id, enrollment_id, amount, status FROM payments');
    }
}

module.exports = { PaymentModel };
