'use strict';

/** Entry point da aplicação — mantém `npm start` (node src/app.js) funcionando. */

const { createApp } = require('./server');

async function main() {
    const { app, logger, settings } = await createApp();

    app.listen(settings.port, () => {
        logger.info(`API rodando na porta ${settings.port}`, { env: settings.appEnv });
    });
}

main().catch((err) => {
    console.error('Falha ao iniciar a aplicação:', err.message);
    process.exit(1);
});
