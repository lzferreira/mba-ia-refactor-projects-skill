const { getDb } = require('./db');

function create(userId, courseId) {
    const db = getDb();
    const result = db.prepare('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)').run(userId, courseId);
    return result.lastInsertRowid;
}

function findByCourseId(courseId) {
    const db = getDb();
    return db.prepare('SELECT * FROM enrollments WHERE course_id = ?').all(courseId);
}

module.exports = { create, findByCourseId };
