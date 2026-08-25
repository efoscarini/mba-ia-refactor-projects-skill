'use strict';

/** Exceções de domínio — traduzidas em resposta HTTP pelo error handler. */

class AppError extends Error {
    constructor(message, status = 500) {
        super(message);
        this.name = this.constructor.name;
        this.status = status;
        this.expected = true;
    }
}

class ValidationError extends AppError {
    constructor(message = 'Bad Request') {
        super(message, 400);
    }
}

class NotFoundError extends AppError {
    constructor(message = 'Recurso não encontrado') {
        super(message, 404);
    }
}

class BusinessError extends AppError {
    constructor(message = 'Operação não permitida') {
        super(message, 400);
    }
}

class UnauthorizedError extends AppError {
    constructor(message = 'Credenciais inválidas') {
        super(message, 401);
    }
}

module.exports = { AppError, ValidationError, NotFoundError, BusinessError, UnauthorizedError };
