from odoo import http
from odoo.http import request


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