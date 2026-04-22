const paymentService = require('../services/paymentService');

function checkout(req, res, next) {
    try {
        const { usr, eml, pwd, c_id, card } = req.body;

        if (!usr || !eml || !c_id || !card) {
            return res.status(400).json({ error: 'Bad Request' });
        }

        const result = paymentService.processCheckout({
            userName: usr,
            email: eml,
            password: pwd,
            courseId: c_id,
            card,
        });

        return res.status(200).json({ msg: 'Sucesso', enrollment_id: result.enrollmentId });
    } catch (err) {
        next(err);
    }
}

module.exports = { checkout };
