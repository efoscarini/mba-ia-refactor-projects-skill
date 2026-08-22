'use strict';

/** Trilha de auditoria. */

class AuditLogModel {
    constructor(db) {
        this.db = db;
    }

    async record(action, executor = this.db) {
        await executor.run(
            "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
            [action],
        );
    }
}

module.exports = { AuditLogModel };
