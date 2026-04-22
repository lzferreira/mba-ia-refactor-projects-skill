const reportService = require('../services/reportService');

function financialReport(req, res, next) {
    try {
        const report = reportService.getFinancialReport();
        return res.json(report);
    } catch (err) {
        next(err);
    }
}

module.exports = { financialReport };
