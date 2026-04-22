const { getDb } = require('./db');

function findByEmail(email) {
    const db = getDb();
    return db.prepare('SELECT id, name, email FROM users WHERE email = ?').get(email);
}

function findById(id) {
    const db = getDb();
    return db.prepare('SELECT id, name, email FROM users WHERE id = ?').get(id);
}

function create(name, email, hashedPassword) {
    const db = getDb();
    const result = db.prepare('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)').run(name, email, hashedPassword);
    return result.lastInsertRowid;
}

function deleteById(id) {
    const db = getDb();
    const deleteTransaction = db.transaction(() => {
        // Clean up related data before deleting user
        const enrollments = db.prepare('SELECT id FROM enrollments WHERE user_id = ?').all(id);
        for (const enrollment of enrollments) {
            db.prepare('DELETE FROM payments WHERE enrollment_id = ?').run(enrollment.id);
        }
        db.prepare('DELETE FROM enrollments WHERE user_id = ?').run(id);
        db.prepare('DELETE FROM users WHERE id = ?').run(id);
    });
    deleteTransaction();
}

module.exports = { findByEmail, findById, create, deleteById };
