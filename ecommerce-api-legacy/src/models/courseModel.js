const { getDb } = require('./db');

function findActiveById(id) {
    const db = getDb();
    return db.prepare('SELECT * FROM courses WHERE id = ? AND active = 1').get(id);
}

function findAll() {
    const db = getDb();
    return db.prepare('SELECT * FROM courses').all();
}

module.exports = { findActiveById, findAll };
