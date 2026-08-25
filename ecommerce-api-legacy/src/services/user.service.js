'use strict';

/**
 * Caso de uso de exclusão de usuário.
 *
 * O handler original apagava só a linha de `users` e devolvia uma mensagem
 * admitindo que matrículas e pagamentos ficavam órfãos. Com as FKs em cascata
 * declaradas no schema, os registros dependentes vão junto, dentro de transação.
 */

const { UnauthorizedError } = require('../middlewares/errors');

class UserService {
    constructor({ db, userModel, auditLogModel, passwordService, authService, logger }) {
        this.db = db;
        this.users = userModel;
        this.auditLogs = auditLogModel;
        this.passwords = passwordService;
        this.auth = authService;
        this.logger = logger;
    }

    /**
     * Emissor de credencial (RF-15). O projeto original não tinha login — sem
     * emissor não há token para o middleware verificar. A rota é aditiva: não
     * altera path, método nem resposta de nenhuma rota existente.
     */
    async login({ email, password }) {
        const user = await this.users.findCredentialsByEmail(email);
        const valid = user && await this.passwords.verify(password, user.pass);
        if (!valid) {
            // Mesma resposta para e-mail inexistente e senha errada: não entrega
            // ao chamador a informação de quais e-mails existem.
            throw new UnauthorizedError('Credenciais inválidas');
        }
        this.logger.info('Login efetuado', { userId: user.id });
        return {
            token: this.auth.issue(user.id),
            user: { id: user.id, name: user.name, email: user.email },
        };
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
