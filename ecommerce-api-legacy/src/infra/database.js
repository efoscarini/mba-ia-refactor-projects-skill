'use strict';

/**
 * Driver SQLite promisificado.
 *
 * Substitui o encadeamento de callbacks do `AppManager`: cada operação devolve
 * uma Promise, e `transaction()` garante que escritas relacionadas (matrícula +
 * pagamento + auditoria) sejam tudo-ou-nada.
 */

const sqlite3 = require('sqlite3');

class Database {
    constructor(path) {
        this._db = new sqlite3.Database(path);
        this._db.run('PRAGMA foreign_keys = ON');
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this._db.run(sql, params, function onDone(err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this._db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        });
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this._db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows || [])));
        });
    }

    /** Executa `fn` dentro de uma transação; qualquer erro faz rollback. */
    async transaction(fn) {
        await this.run('BEGIN');
        try {
            const result = await fn(this);
            await this.run('COMMIT');
            return result;
        } catch (err) {
            await this.run('ROLLBACK').catch(() => {});
            throw err;
        }
    }

    close() {
        return new Promise((resolve) => this._db.close(() => resolve()));
    }
}

module.exports = { Database };
