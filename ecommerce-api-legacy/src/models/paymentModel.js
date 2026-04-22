const { getDb } = require('./db');

function create(enrollmentId, amount, status) {
    const db = getDb();
    const result = db.prepare('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)').run(enrollmentId, amount, status);
    return result.lastInsertRowid;
}

function findByEnrollmentId(enrollmentId) {
    const db = getDb();
    return db.prepare('SELECT amount, status FROM payments WHERE enrollment_id = ?').get(enrollmentId);
}

module.exports = { create, findByEnrollmentId };
