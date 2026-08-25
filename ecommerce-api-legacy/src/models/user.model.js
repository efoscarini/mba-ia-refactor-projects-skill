'use strict';

/** Acesso a dados de usuários. Único lugar com SQL da tabela `users`. */

class UserModel {
    constructor(db) {
        this.db = db;
    }

    findByEmail(email) {
        return this.db.get('SELECT id, name, email FROM users WHERE email = ?', [email]);
    }

    findById(id) {
        return this.db.get('SELECT id, name, email FROM users WHERE id = ?', [id]);
    }

    /** Único ponto que lê a coluna `pass` — usado só na verificação de login. */
    findCredentialsByEmail(email) {
        return this.db.get('SELECT id, name, email, pass FROM users WHERE email = ?', [email]);
    }

    /** Nomes dos alunos de uma lista de ids em uma query só (evita N+1). */
    async findManyByIds(ids) {
        if (ids.length === 0) return new Map();
        const placeholders = ids.map(() => '?').join(',');
        const rows = await this.db.all(
            `SELECT id, name, email FROM users WHERE id IN (${placeholders})`,
            ids,
        );
        return new Map(rows.map((row) => [row.id, row]));
    }

    async create({ name, email, passwordHash }) {
        const result = await this.db.run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            [name, email, passwordHash],
        );
        return { id: result.lastID, name, email };
    }

    /** As FKs em cascata cuidam de enrollments e payments. */
    async deleteById(id) {
        const result = await this.db.run('DELETE FROM users WHERE id = ?', [id]);
        return result.changes;
    }
}

module.exports = { UserModel };
