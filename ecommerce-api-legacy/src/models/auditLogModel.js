const { getDb } = require('./db');

function create(action) {
    const db = getDb();
    db.prepare("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))").run(action);
}

module.exports = { create };
