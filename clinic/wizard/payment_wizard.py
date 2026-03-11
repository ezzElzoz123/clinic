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

    @api.depends('insurance_percentage')
    def _compute_insurance_amount(self):
        for rec in self:
            rec.insurance_amount = rec.medical_visit_id.total_cost * (rec.insurance_percentage / 100)
            rec.patient_amount = rec.medical_visit_id.total_cost - rec.insurance_amount

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        medical_visit_id = self.env.context.get('active_id')
        journal_cash = self.env['account.journal'].search([('type', '=', 'cash')], limit=1)
        if medical_visit_id:
            res['medical_visit_id'] = int(medical_visit_id)
            res['journal_id'] = journal_cash.id
        return res

    def action_confirm(self):
        if self.amount <= 0 and self.insurance_percentage != 100:
            raise ValidationError(_("Paid amount should be positive number"))
        if self.insurance_percentage <= 0 or self.insurance_percentage > 100:
            if self.env.lang == 'en_us':
                raise ValidationError(_("Insurance percentage should be between 0 and 100"))
            else:
                raise ValidationError(_("الرجاء إدخال نسبة تغطية صحيحة لشركة التأمين (من 0 إلى 100%)."))
        payment_method = self.journal_id.inbound_payment_method_line_ids[:1].payment_method_id
        visit = self.medical_visit_id
        if not visit.invoice_id:
            visit.action_create_invoice()
        invoice = visit.invoice_id
        payment = self.env['account.payment'].create({
            'partner_id': self.medical_visit_id.patient_id.partner_id.id,
            'amount': self.amount,
            'currency_id': self.medical_visit_id.currency_id.id,
            'journal_id': self.journal_id.id,
            'payment_type': 'inbound',
            'payment_method_line_id': self.journal_id.inbound_payment_method_line_ids[:1].id,
            'ref': f'Advance Payment for {self.medical_visit_id.patient_id.name}',
        })
        visit.has_insurance = True
        payment.action_post()
        if invoice.state == 'draft':
            invoice.action_post()
        # invoice.action_post()

        # reconciliation
        (payment.line_ids + invoice.line_ids) \
            .filtered(
            lambda line: line.account_id == invoice.partner_id.property_account_receivable_id and not line.reconciled) \
            .reconcile()

        visit.advance_payment_ids |= payment
        visit.advance_payment_amount += self.amount
        if visit.advance_payment_amount >= visit.total_cost:
            if self.env.lang == 'en_US':
                raise ValidationError(_("The visit is already fully paid. No additional payment can be added."))
            else:
                raise ValidationError(_("لا يمكن إضافة دفعة جديدة، فقد تم سداد كامل تكلفة الكشف."))