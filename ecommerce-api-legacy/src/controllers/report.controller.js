'use strict';

/** Orquestração do relatório financeiro. */

class ReportController {
    constructor(reportService) {
        this.reports = reportService;
    }

    async financial(req, res) {
        res.json(await this.reports.financial());
    }
}

module.exports = { ReportController };
