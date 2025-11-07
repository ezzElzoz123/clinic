""" Initialize Account Move """
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError, Warning


class AccountMove(models.Model):
    _inherit = 'account.move'

    medical_visit_id = fields.Many2one('medical.visit', string="Medical Visit", readonly=True)
    sequence_name = fields.Char(string="Invoice Sequence", copy=False, readonly=True, index=True)

    @api.model
    def create(self, vals):
        if vals.get("sequence_name", "Draft") == "Draft":
            vals["sequence_name"] = self.env["ir.sequence"].next_by_code("account.move") or "Draft"
        return super(AccountMove, self).create(vals)