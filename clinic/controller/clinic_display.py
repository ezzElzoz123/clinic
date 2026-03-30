from odoo import http
from odoo.http import request
import json

class ClinicDisplay(http.Controller):

    @http.route('/clinic/display', type='http', auth='public')
    def display(self, **kw):
        request.env['medical.visit'].sudo().action_ensure_in_progress()
        visits = request.env['medical.visit'].sudo().search(
            [('status', 'in', ['waiting', 'in_progress'])],
            order='name asc',
        )
        departments = request.env['medical.department'].sudo().search([])
        return request.render('clinic.display_screen', {
            'visits': visits,
            'departments': departments,
        })

    @http.route('/clinic/last_called', type='http', auth='public', csrf=False)
    def last_called(self, **kw):
        """يرجع آخر مريض اتنادى عليه للـ TTS"""
        visit = request.env['medical.visit'].sudo().search(
            [('status', '=', 'in_progress')],
            order='write_date desc',
            limit=1,
        )
        if visit:
            return request.make_response(
                json.dumps({
                    'number': visit.name,
                    'department': visit.department_id.name or '',
                }),
                headers=[('Content-Type', 'application/json')]
            )
        return request.make_response(
            json.dumps({'number': None}),
            headers=[('Content-Type', 'application/json')]
        )