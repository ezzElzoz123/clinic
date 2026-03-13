from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AdvancePaymentWizard(models.TransientModel):
    _name = 'advance.payment.wizard'
    _description = 'Advance Payment Wizard'

    medical_visit_id = fields.Many2one('medical.visit', string="Medical Visit", required=True)
    amount = fields.Monetary(string="Advance Amount", required=True)
    currency_id = fields.Many2one(related='medical_visit_id.currency_id', readonly=True)
    journal_id = fields.Many2one('account.journal', string="Payment Journal", required=True)
    insurance_company_id = fields.Many2one('insurance.company', string="Insurance Company")
    insurance_percentage = fields.Integer(string="Insurance Coverage %")
    insurance_amount = fields.Monetary(string="Insurance Amount", compute="_compute_insurance_amount")
    patient_amount = fields.Monetary(string="Patient Amount", compute="_compute_insurance_amount")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        visit_id = self.env.context.get('active_id')
        visit = self.env['medical.visit'].browse(visit_id)

        journal_cash = self.env['account.journal'].search([('type', '=', 'cash')], limit=1)

        if visit:
            res.update({
                'medical_visit_id': visit.id,
                'journal_id': journal_cash.id,
                'insurance_company_id': visit.insurance_company_id.id,
                'insurance_percentage': visit.insurance_percentage,
            })

        return res

    @api.depends('insurance_percentage', 'medical_visit_id.total_cost')
    def _compute_insurance_amount(self):
        for rec in self:
            rec.insurance_amount = rec.medical_visit_id.total_cost * (rec.insurance_percentage / 100)
            rec.patient_amount = rec.medical_visit_id.total_cost - rec.insurance_amount

    def action_confirm(self):
        visit = self.medical_visit_id
        # تحقق من التأمين
        if self.insurance_company_id:
            if not 0 < self.insurance_percentage <= 100:
                raise ValidationError(_("Insurance percentage must be between 0 and 100"))
            visit.write({
                'insurance_company_id': self.insurance_company_id.id,
                'insurance_percentage': self.insurance_percentage,
                'has_insurance': True
            })
        # المبلغ المستحق على المريض
        patient_due = visit.patient_amount if visit.insurance_company_id else visit.total_cost
        if self.amount <= 0 and patient_due != 0:
            raise ValidationError(_("Payment amount must be greater than zero"))
        new_total_paid = visit.advance_payment_amount + self.amount
        if new_total_paid > patient_due:
            raise ValidationError(_("Payment exceeds the patient's due amount"))
        # إنشاء الفاتورة
        if not visit.invoice_id:
            visit.action_create_invoice()
        invoice = visit.invoice_id
        # إنشاء الدفع
        payment = self.env['account.payment'].create({
            'partner_id': visit.patient_id.partner_id.id,
            'amount': self.amount,
            'currency_id': visit.currency_id.id,
            'journal_id': self.journal_id.id,
            'payment_type': 'inbound',
            'payment_method_line_id': self.journal_id.inbound_payment_method_line_ids[:1].id,
            'date': fields.Date.today(),
            'ref': f'Advance Payment for {visit.patient_id.name}',
        })
        payment.action_post()
        if invoice.state == 'draft':
            invoice.action_post()
        # reconciliation
        (payment.line_ids + invoice.line_ids).filtered(
            lambda line: line.account_id == invoice.partner_id.property_account_receivable_id
                         and not line.reconciled
        ).reconcile()
        visit.advance_payment_ids |= payment
        visit.advance_payment_amount = new_total_paid
        return {'type': 'ir.actions.act_window_close'}