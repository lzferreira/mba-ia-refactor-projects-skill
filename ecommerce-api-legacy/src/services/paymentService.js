const { getDb } = require('../models/db');
const bcrypt = require('bcryptjs');
const courseModel = require('../models/courseModel');
const userModel = require('../models/userModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditLogModel = require('../models/auditLogModel');

const SALT_ROUNDS = 10;

function processCheckout({ userName, email, password, courseId, card }) {
    const course = courseModel.findActiveById(courseId);
    if (!course) {
        const err = new Error('Curso não encontrado');
        err.status = 404;
        throw err;
    }

    let userId;
    const existingUser = userModel.findByEmail(email);

    if (existingUser) {
        userId = existingUser.id;
    } else {
        const hashedPassword = bcrypt.hashSync(password || '', SALT_ROUNDS);
        userId = userModel.create(userName, email, hashedPassword);
    }

    const paymentStatus = simulatePayment(card);
    if (paymentStatus === 'DENIED') {
        const err = new Error('Pagamento recusado');
        err.status = 400;
        throw err;
    }

    // Transaction: enrollment + payment + audit log are atomic
    const db = getDb();
    const checkoutTransaction = db.transaction(() => {
        const enrollmentId = enrollmentModel.create(userId, courseId);
        paymentModel.create(enrollmentId, course.price, paymentStatus);
        auditLogModel.create(`Checkout curso ${courseId} por ${userId}`);
        return enrollmentId;
    });

    const enrollmentId = checkoutTransaction();

    return { enrollmentId };
}

function simulatePayment(card) {
    // Placeholder for real gateway integration
    return card.startsWith('4') ? 'PAID' : 'DENIED';
}

module.exports = { processCheckout };
