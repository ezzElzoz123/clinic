from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError, Warning

class MedicalOperationLine(models.Model):
    _name = 'medical.operation.line'
    _description = 'Medical Operation Line'

    visit_id = fields.Many2one('medical.visit', string='Visit', ondelete='cascade', tracking=True)
    product_id = fields.Many2one('product.product', string='Procedure / Product', required=True, tracking=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    price_unit = fields.Float(string='Unit Price', related='product_id.list_price', readonly=False, tracking=True)
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True, tracking=True)

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit
