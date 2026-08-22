'use strict';

/**
 * Caso de uso de exclusão de usuário.
 *
 * O handler original apagava só a linha de `users` e devolvia uma mensagem
 * admitindo que matrículas e pagamentos ficavam órfãos. Com as FKs em cascata
 * declaradas no schema, os registros dependentes vão junto, dentro de transação.
 */

class UserService {
    constructor({ db, userModel, auditLogModel, logger }) {
        this.db = db;
        this.users = userModel;
        this.auditLogs = auditLogModel;
        this.logger = logger;
    }

    async delete(userId) {
        const removed = await this.db.transaction(async (tx) => {
            const changes = await this.users.deleteById(userId);
            await this.auditLogs.record(`Usuario ${userId} removido`, tx);
            return changes;
        });

        this.logger.info('Usuário removido', { userId, removed });
        return removed;
    }
}

module.exports = { UserService };
