'use strict';

/** Orquestração da exclusão de usuário. */

const { validateUserId } = require('../middlewares/validators');

class UserController {
    constructor(userService) {
        this.users = userService;
    }

    async remove(req, res) {
        const userId = validateUserId(req.params);
        await this.users.delete(userId);
        res.send('Usuário deletado.');
    }
}

module.exports = { UserController };
