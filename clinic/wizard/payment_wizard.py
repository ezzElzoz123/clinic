from odoo import models, fields, api

class AdvancePaymentWizard(models.TransientModel):
    _name = 'advance.payment.wizard'
    _description = 'Advance Payment Wizard'

    medical_visit_id = fields.Many2one('medical.visit', string="Medical Visit", required=True)
    amount = fields.Monetary(string="Advance Amount", required=True)
    currency_id = fields.Many2one(related='medical_visit_id.currency_id', readonly=True)
    journal_id = fields.Many2one('account.journal', string="Payment Journal", required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        medical_visit_id = self.env.context.get('active_id')
        if medical_visit_id:
            res['medical_visit_id'] = int(medical_visit_id)
        return res

    def action_confirm(self):
        payment = self.env['account.payment'].create({
            'partner_id': self.medical_visit_id.patient_id.partner_id.id,
            'amount': self.amount,
            'currency_id': self.medical_visit_id.currency_id.id,
            'journal_id': self.journal_id.id,
            'payment_type': 'inbound',
            'payment_method_line_id': self.env.ref('account.account_payment_method_manual_in').id,
            'ref': f'Advance Payment for {self.medical_visit_id.patient_id.name}',
        })
        payment.action_post()

        self.medical_visit_id.advance_payment_ids |= payment
        self.medical_visit_id.advance_payment_amount = self.amount
        return {'type': 'ir.actions.act_window_close'}