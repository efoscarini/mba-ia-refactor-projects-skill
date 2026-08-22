'use strict';

/** Orquestração do checkout: valida, delega ao service e monta a resposta. */

const { validateCheckout } = require('../middlewares/validators');

class CheckoutController {
    constructor(checkoutService) {
        this.checkout = checkoutService;
    }

    async create(req, res) {
        const input = validateCheckout(req.body);
        const { enrollmentId } = await this.checkout.execute(input);
        res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    }
}

module.exports = { CheckoutController };
