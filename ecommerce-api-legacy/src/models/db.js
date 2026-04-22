const Database = require('better-sqlite3');

let db;

function initDb(dbPath = ':memory:') {
    db = new Database(dbPath);
    db.pragma('journal_mode = WAL');
    db.pragma('foreign_keys = ON');

    db.exec(`
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            pass TEXT
        )
    `);
    db.exec(`
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY,
            title TEXT,
            price REAL,
            active INTEGER
        )
    `);
    db.exec(`
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            course_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    `);
    db.exec(`
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY,
            enrollment_id INTEGER,
            amount REAL,
            status TEXT,
            FOREIGN KEY (enrollment_id) REFERENCES enrollments(id)
        )
    `);
    db.exec(`
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY,
            action TEXT,
            created_at DATETIME
        )
    `);

    // Seeds
    const userCount = db.prepare('SELECT COUNT(*) as count FROM users').get();
    if (userCount.count === 0) {
        const bcrypt = require('bcryptjs');
        const hashedPass = bcrypt.hashSync('123', 10);

        db.prepare('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)').run('Leonan', 'leonan@fullcycle.com.br', hashedPass);
        db.prepare("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1)").run();
        db.prepare("INSERT INTO courses (title, price, active) VALUES ('Docker', 497.00, 1)").run();
        db.prepare('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)').run();
        db.prepare("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')").run();
    }

    return db;
}

function getDb() {
    if (!db) {
        throw new Error('Database not initialized. Call initDb() first.');
    }
    return db;
}

module.exports = { initDb, getDb };
