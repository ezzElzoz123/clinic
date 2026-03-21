from odoo import _, api, models, fields
from odoo.exceptions import ValidationError


class InsuranceCompany(models.Model):
    _name = "insurance.company"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "sequence desc"
    _description = "Insurance Company"

    sequence = fields.Integer(string='Sequence' ,tracking=True)
    name = fields.Char(string='Company Name' ,tracking=True, required=True)
    start_date = fields.Date(string='Start Date' ,tracking=True)
    end_date = fields.Date(string='End Date' ,tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('expired', 'Expired'),
        ('cancel', 'Cancelled'),
    ], default='draft' ,tracking=True)

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_confirm(self):
        for rec in self:
            rec.state = 'running'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    @api.model
    def action_expire(self):  # scheduled action
        insurances = self.env['insurance.company'].search([])
        today = fields.Date.today()
        for rec in insurances:
            if rec.end_date and rec.end_date < today:
                rec.state = 'expired'
