from odoo import fields, models, api

class MedicalVisitProductLine(models.Model):
    _name = 'medical.visit.product.line'
    _description = 'Products Used During Visit'

    visit_id = fields.Many2one('medical.visit', string='Visit', ondelete='cascade',tracking=True)
    product_id = fields.Many2one('product.product', string='Product', required=True,tracking=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    price_unit = fields.Float(string='Unit Price', related='product_id.list_price', readonly=False,tracking=True)
    currency_id = fields.Many2one('res.currency', related='visit_id.currency_id', store=True, readonly=False,tracking=True)
    subtotal = fields.Monetary(string='Subtotal', compute='_compute_subtotal', store=True,tracking=True)

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit
