const { getDb } = require('../models/db');

function getFinancialReport() {
    const db = getDb();

    // Single JOIN query instead of N+1
    const rows = db.prepare(`
        SELECT
            c.id AS course_id,
            c.title AS course_title,
            u.name AS student_name,
            p.amount,
            p.status
        FROM courses c
        LEFT JOIN enrollments e ON e.course_id = c.id
        LEFT JOIN users u ON u.id = e.user_id
        LEFT JOIN payments p ON p.enrollment_id = e.id
    `).all();

    // Group results by course
    const coursesMap = new Map();

    for (const row of rows) {
        if (!coursesMap.has(row.course_id)) {
            coursesMap.set(row.course_id, {
                course: row.course_title,
                revenue: 0,
                students: [],
            });
        }

        const courseData = coursesMap.get(row.course_id);

        if (row.student_name) {
            if (row.status === 'PAID') {
                courseData.revenue += row.amount;
            }
            courseData.students.push({
                student: row.student_name,
                paid: row.amount || 0,
            });
        }
    }

    return Array.from(coursesMap.values());
}

module.exports = { getFinancialReport };
