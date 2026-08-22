'use strict';

/** Acesso a dados de cursos. */

class CourseModel {
    constructor(db) {
        this.db = db;
    }

    findActiveById(id) {
        return this.db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
    }

    listAll() {
        return this.db.all('SELECT * FROM courses ORDER BY id');
    }
}

module.exports = { CourseModel };
