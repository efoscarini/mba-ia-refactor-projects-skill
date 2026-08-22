'use strict';

/**
 * Relatório financeiro por curso.
 *
 * O original disparava 1 + N + (N*M*2) queries com contadores manuais de
 * pendência (`coursesPending--`, `enrPending--`) para decidir quando responder.
 * Aqui são 4 queries, sempre, e a ordem do resultado é determinística.
 */

const { PAYMENT_STATUS } = require('../config/constants');

class ReportService {
    constructor({ courseModel, enrollmentModel, paymentModel, userModel }) {
        this.courses = courseModel;
        this.enrollments = enrollmentModel;
        this.payments = paymentModel;
        this.users = userModel;
    }

    async financial() {
        const [courses, enrollments, payments] = await Promise.all([
            this.courses.listAll(),
            this.enrollments.listAll(),
            this.payments.listAll(),
        ]);

        const userIds = [...new Set(enrollments.map((e) => e.user_id))];
        const usersById = await this.users.findManyByIds(userIds);

        const paymentByEnrollment = new Map(payments.map((p) => [p.enrollment_id, p]));
        const enrollmentsByCourse = new Map();
        for (const enrollment of enrollments) {
            const list = enrollmentsByCourse.get(enrollment.course_id) || [];
            list.push(enrollment);
            enrollmentsByCourse.set(enrollment.course_id, list);
        }

        return courses.map((course) => {
            const courseEnrollments = enrollmentsByCourse.get(course.id) || [];
            let revenue = 0;
            const students = [];

            for (const enrollment of courseEnrollments) {
                const payment = paymentByEnrollment.get(enrollment.id);
                const user = usersById.get(enrollment.user_id);

                if (payment && payment.status === PAYMENT_STATUS.PAID) {
                    revenue += payment.amount;
                }
                students.push({
                    student: user ? user.name : 'Unknown',
                    paid: payment ? payment.amount : 0,
                });
            }

            return { course: course.title, revenue, students };
        });
    }
}

module.exports = { ReportService };
