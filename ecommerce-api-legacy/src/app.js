const express = require('express');
const config = require('./config');
const { initDb } = require('./models/db');
const routes = require('./routes');
const errorHandler = require('./middlewares/errorHandler');

const app = express();
app.use(express.json());

// Initialize database
initDb(config.dbPath);

// Register routes
app.use(routes);

// Central error handler (must be after routes)
app.use(errorHandler);

app.listen(config.port, () => {
    console.log(`ecommerce-api-legacy running on port ${config.port}`);
});
