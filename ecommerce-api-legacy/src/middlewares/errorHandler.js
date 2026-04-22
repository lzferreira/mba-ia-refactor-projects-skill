function errorHandler(err, req, res, _next) {
    const status = err.status || 500;
    const message = status === 500 ? 'Internal server error' : err.message;

    if (status === 500) {
        console.error('[ERROR]', err.stack || err.message);
    }

    return res.status(status).json({ error: message });
}

module.exports = errorHandler;
