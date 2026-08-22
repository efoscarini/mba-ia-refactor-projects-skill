'use strict';

/**
 * Schema e carga inicial.
 *
 * Antes vivia dentro do `AppManager.initDb()`, misturado à abertura da conexão
 * e ao registro de rotas. As FKs agora são declaradas — os `enrollments` e
 * `payments` órfãos que o projeto original deixava para trás passam a ser
 * removidos em cascata.
 */

const TABLES = [
    `CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        pass TEXT NOT NULL
    )`,
    `CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        price REAL NOT NULL,
        active INTEGER NOT NULL DEFAULT 1
    )`,
    `CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        course_id INTEGER REFERENCES courses(id)
    )`,
    `CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY,
        enrollment_id INTEGER REFERENCES enrollments(id) ON DELETE CASCADE,
        amount REAL NOT NULL,
        status TEXT NOT NULL
    )`,
    `CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY,
        action TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`,
];

const SEED_COURSES = [
    { title: 'Clean Architecture', price: 997.0, active: 1 },
    { title: 'Docker', price: 497.0, active: 1 },
];

const SEED_USER = { name: 'Leonan', email: 'leonan@fullcycle.com.br' };

async function createSchema(db) {
    for (const ddl of TABLES) {
        await db.run(ddl);
    }
}

/**
 * Carga idempotente. A senha do usuário de exemplo entra com hash — o projeto
 * original gravava a string '123' em texto plano.
 */
async function seed(db, { hashPassword, seedPassword }) {
    const { total } = await db.get('SELECT COUNT(*) AS total FROM courses');
    if (total > 0) return;

    const userResult = await db.run(
        'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        [SEED_USER.name, SEED_USER.email, await hashPassword(seedPassword)],
    );

    const courseIds = [];
    for (const course of SEED_COURSES) {
        const result = await db.run(
            'INSERT INTO courses (title, price, active) VALUES (?, ?, ?)',
            [course.title, course.price, course.active],
        );
        courseIds.push(result.lastID);
    }

    const enrollment = await db.run(
        'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
        [userResult.lastID, courseIds[0]],
    );
    await db.run(
        'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
        [enrollment.lastID, SEED_COURSES[0].price, 'PAID'],
    );
}

module.exports = { createSchema, seed };
