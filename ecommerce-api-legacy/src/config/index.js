const config = {
    port: parseInt(process.env.PORT, 10) || 3000,
    dbPath: process.env.DB_PATH || ':memory:',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    smtpUser: process.env.SMTP_USER || '',
    logLevel: process.env.LOG_LEVEL || 'info',
};

module.exports = config;
