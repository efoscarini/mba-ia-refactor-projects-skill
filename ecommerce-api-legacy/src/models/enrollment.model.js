'use strict';

/** Acesso a dados de matrículas. */

class EnrollmentModel {
    constructor(db) {
        this.db = db;
    }

    async create({ userId, courseId }, executor = this.db) {
        const result = await executor.run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [userId, courseId],
        );
        return result.lastID;
    }

    /** Todas as matrículas de uma vez, para o relatório montar em memória. */
    listAll() {
        return this.db.all('SELECT id, user_id, course_id FROM enrollments ORDER BY id');
    }
}

module.exports = { EnrollmentModel };
