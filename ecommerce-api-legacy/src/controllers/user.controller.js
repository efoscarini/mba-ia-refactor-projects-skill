'use strict';

/** Orquestração da exclusão de usuário. */

const { validateUserId, validateLogin } = require('../middlewares/validators');

class UserController {
    constructor(userService) {
        this.users = userService;
    }

    async remove(req, res) {
        const userId = validateUserId(req.params);
        await this.users.delete(userId);
        res.send('Usuário deletado.');
    }

    async login(req, res) {
        const credentials = validateLogin(req.body);
        res.json(await this.users.login(credentials));
    }
}

module.exports = { UserController };
