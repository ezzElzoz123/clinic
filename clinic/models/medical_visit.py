from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import pytz
from datetime import datetime, timedelta


class MedicalVisit(models.Model):
    _name = 'medical.visit'
    _description = 'Medical Visit'
    _rec_name = 'patient_id'
    _order = 'date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # =========================
    # 🔹 Basic Info
    # =========================
    patient_id = fields.Many2one('medical.patient', string="Patient", required=True, tracking=True)
    company_id = fields.Many2one('res.company', string="Clinic", default=lambda self: self.env.company.id)
    doctor_id = fields.Many2one('medical.doctor', string="Doctor", required=True, tracking=True)
    available_doctor_ids = fields.Many2many('medical.doctor', string="Doctors", compute='_compute_available_doctor_ids')
    department_id = fields.Many2one('medical.department', string="Department", tracking=True)
    date = fields.Datetime(string="Visit Date", default=fields.Datetime.now, required=True)
    date_end = fields.Datetime()
    duration_minutes = fields.Integer(string="Duration (Minutes)", default=10, help="Duration of the visit in minutes")
    visit_type = fields.Selection([
        ('consultation', 'Consultation'),
        ('followup', 'Follow-up'),
    ], string="Visit Type", required=True, tracking=True)
    cancel_reason = fields.Text(string="Cancellation Reason", tracking=True)

    # =========================
    # 🔹 Personal Info
    # =========================
    age = fields.Integer(string="Age")
    occupation = fields.Char(string="Occupation")
    birth_date = fields.Date(string="Birth Date")
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string="Gender", required=True)
    phone_no = fields.Char(string="Phone Number", size=11, help="Enter patient's contact number.", tracking=True)
    address = fields.Char(string="Address", help="Enter full address including city and street.")
    marital_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widow', 'Widow'),
    ], string="Marital Status", default='single', tracking=True)
    childern_number = fields.Integer()
    last_child_age = fields.Integer()

    # =========================
    # 🔹 Female Section
    # =========================
    is_pregnant = fields.Boolean(string="Pregnant", tracking=True)
    pregnant_at_month = fields.Integer(string="Pregnant At Month", tracking=True)
    pregnancy_weeks = fields.Integer(string="Pregnancy Weeks", tracking=True)
    last_menstrual_period = fields.Date(string="Last Menstrual Period", tracking=True)
    menstrual_history = fields.Text(string="Menstrual History", tracking=True)
    contraception_method = fields.Selection([
        ('none', 'None'),
        ('pill', 'Pill'),
        ('iud', 'IUD'),
        ('implant', 'Implant'),
        ('condom', 'Condom'),
        ('other', 'Other'),
    ], string="Contraception Method", tracking=True)
    gynecology_notes = fields.Text(string="Gynecology Notes", tracking=True)

    # =========================
    # 🔹 Attachments
    # =========================
    xray_attachment_ids = fields.Many2many(
        'ir.attachment', 'medical_visit_xray_rel', 'visit_id', 'attachment_id', string="X-Ray Attachments", tracking=True
    )
    prescription_attachment_ids = fields.Many2many(
        'ir.attachment', 'medical_visit_prescription_rel', 'visit_id', 'attachment_id',
        string="Prescription Attachments", tracking=True
    )
    lab_attachment_ids = fields.Many2many(
        'ir.attachment', 'medical_visit_lab_rel', 'visit_id', 'attachment_id', string="Lab Test Attachments", tracking=True
    )

    # =========================
    # 🔹 Vitals (Examination)
    # =========================
    blood_pressure = fields.Char(string="Blood Pressure", tracking=True)
    heart_rate = fields.Integer(string="Heart Rate (bpm)", tracking=True)
    temperature = fields.Float(string="Temperature (°C)", tracking=True)
    weight = fields.Float(string="Weight (kg)", tracking=True)
    height = fields.Float(string="Height (cm)", tracking=True)
    bmi = fields.Float(string="BMI", compute="_compute_bmi", store=True, tracking=True)

    # =========================
    # 🔹 Medical History
    # =========================
    has_diabetes = fields.Boolean(string="Diabetes", tracking=True)
    has_hypertension = fields.Boolean(string="Hypertension", tracking=True)
    has_heart_disease = fields.Boolean(string="Heart Disease", tracking=True)
    has_kidney_disease = fields.Boolean(string="Kidney Disease", tracking=True)
    has_liver_disease = fields.Boolean(string="Liver Disease", tracking=True)
    allergies = fields.Text(string="Allergies", tracking=True)
    current_medications = fields.Text(string="Current Medications", tracking=True)
    smoking = fields.Boolean(string="Smoker", tracking=True)
    alcohol = fields.Boolean(string="Alcohol Consumption", tracking=True)
    previous_surgeries = fields.Text(string="Previous Surgeries", tracking=True)
    physical_activity_level = fields.Selection([
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
    ], string="Physical Activity Level", tracking=True)
    medical_history_notes = fields.Text(string="Medical History Notes", tracking=True)
    has_medical_risk = fields.Boolean(
        string="Has Medical Risk",
        compute="_compute_has_medical_risk",
        store=True
    )

    # =========================
    # 🔹 Diagnosis & Treatment
    # =========================
    complaint = fields.Text(string="Complaint", tracking=True)
    diagnosis = fields.Text(string="Diagnosis", tracking=True)
    next_visit_date = fields.Date(string="Next Visit Date", tracking=True)
    recommendations = fields.Text(string="Recommendations", tracking=True)
    prescription_ids = fields.Many2many('medical.prescription', string="Prescription", tracking=True)
    radiology_required = fields.Text(tracking=True)
    lab_required = fields.Text(tracking=True)

    # =========================
    # 🔹 Accounting
    # =========================
    price = fields.Float(string="Consultation Price", required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id, required=True, tracking=True)
    advance_payment_ids = fields.Many2many('account.payment', string="Advance Payment")
    advance_payment_amount = fields.Float(string="Paid Amount")
    total_cost = fields.Float(string="Total Cost", compute="_compute_total_cost", store=True)
    invoice_id = fields.Many2one('account.move', string="Invoice", readonly=True, ondelete="set null", tracking=True)
    invoice_state = fields.Selection(
        related="invoice_id.payment_state",
        string="Payment Status",
        store=True,
        tracking=True
    )
    
    # =========================
    # 🔹 Operations & Procedures
    # =========================
    operation_line_ids = fields.One2many('medical.operation.line', 'visit_id', string='Procedures / Operations', tracking=True)
    operation_total = fields.Monetary(string='Operation Total', compute='_compute_operation_total', store=True, tracking=True)

    # =========================
    # 🔹 Products
    # =========================
    product_line_ids = fields.One2many('medical.visit.product.line','visit_id',string='Used Products',tracking=True)
    product_total = fields.Monetary(string='Products Total', compute='_compute_product_total', store=True, tracking=True)

    # =========================
    # 🔹 State Tracking
    # =========================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('invoiced', 'Invoiced'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string="Status", default="draft", tracking=True)
    # =========================
    # 🔹 Insurance
    # =========================
    has_insurance = fields.Boolean('Has Insurance', tracking=True)
    insurance_company_id = fields.Many2one(
        'insurance.company',
        string="Insurance Company",
        tracking=True
    )
    insurance_percentage = fields.Integer(
        string="Insurance Coverage %",
        tracking=True
    )
    insurance_amount = fields.Monetary(
        string="Insurance Amount",
        compute="_compute_insurance_amount",
        store=True
    )
    patient_amount = fields.Monetary(
        string="Patient Amount",
        compute="_compute_insurance_amount",
        store=True
    )

    # =========================
    # 🔹 COMPUTE METHODS
    # =========================
    @api.depends('weight', 'height')
    def _compute_bmi(self):
        for rec in self:
            rec.bmi = rec.weight / ((rec.height / 100) ** 2) if rec.height and rec.weight else 0.0

    @api.depends('operation_line_ids.subtotal')
    def _compute_operation_total(self):
        for rec in self:
            rec.operation_total = sum(rec.operation_line_ids.mapped('subtotal'))

    @api.depends('product_line_ids.subtotal')
    def _compute_product_total(self):
        for rec in self:
            rec.product_total = sum(rec.product_line_ids.mapped('subtotal'))

    @api.depends('operation_total', 'product_total', 'price')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = rec.price + rec.operation_total + rec.product_total


    @api.depends("date", "department_id")
    def _compute_available_doctor_ids(self):
        days_map = {
            0: "monday", 1: "tuesday", 2: "wednesday",
            3: "thursday", 4: "friday", 5: "saturday", 6: "sunday",
        }

        for rec in self:
            rec.available_doctor_ids = False
            if not rec.date or not rec.department_id:
                continue

            user_tz = self.env.user.tz or "UTC"
            tz = pytz.timezone(user_tz)
            local_dt = pytz.UTC.localize(rec.date).astimezone(tz)

            weekday = local_dt.weekday()
            day_name = days_map.get(weekday)
            visit_time = local_dt.time()
            visit_float = visit_time.hour + visit_time.minute / 60.0

            doctors = self.env["medical.doctor"].search([("department_id", "=", rec.department_id.id)])
            available = doctors.filtered(
                lambda d: any(s.day_of_week == day_name and s.start_time <= visit_float <= s.end_time for s in d.schedule_ids)
            )
            rec.available_doctor_ids = available

    @api.depends('insurance_percentage', 'total_cost')
    def _compute_insurance_amount(self):
        for rec in self:
            if rec.insurance_company_id:
                rec.insurance_amount = rec.total_cost * (rec.insurance_percentage / 100)
            else:
                rec.insurance_amount = 0.0

            rec.patient_amount = rec.total_cost - rec.insurance_amount

    @api.depends(
        'has_diabetes',
        'has_hypertension',
        'has_heart_disease',
        'has_kidney_disease',
        'has_liver_disease',
        'allergies',
        'smoking',
        'alcohol'
    )
    def _compute_has_medical_risk(self):
        for rec in self:
            rec.has_medical_risk = any([
                rec.has_diabetes,
                rec.has_hypertension,
                rec.has_heart_disease,
                rec.has_kidney_disease,
                rec.has_liver_disease,
                rec.smoking,
                rec.alcohol,
                bool(rec.allergies),
            ])

    # =========================
    # 🔹 ONCHANGE & CONSTRAINS
    # =========================
    @api.onchange("date", "duration_minutes")
    @api.constrains("date", "duration_minutes")
    def _onchange_date(self):
        for rec in self:
            if rec.date:
                rec.date_end = rec.date + timedelta(minutes=rec.duration_minutes)

    @api.onchange("patient_id")
    def _onchange_patient_id(self):
        for rec in self:
            if rec.patient_id:
                p = rec.patient_id
                rec.update({
                    'age': p.age,
                    'gender': p.gender,
                    'occupation': p.occupation,
                    'phone_no': p.phone_no,
                    'address': p.address,
                    'has_diabetes': p.has_diabetes,
                    'has_hypertension': p.has_hypertension,
                    'has_heart_disease': p.has_heart_disease,
                    'has_kidney_disease': p.has_kidney_disease,
                    'has_liver_disease': p.has_liver_disease,
                    'allergies': p.allergies,
                    'current_medications': p.current_medications,
                    'previous_surgeries': p.previous_surgeries,
                    'smoking': p.smoking,
                    'alcohol': p.alcohol,
                    'physical_activity_level': p.physical_activity_level,
                })

    @api.constrains('doctor_id', 'date')
    def _check_visit_overlap(self):
        for rec in self:
            if not rec.doctor_id or not rec.date:
                continue
            start_dt = rec.date
            end_dt = rec.date + timedelta(minutes=rec.duration_minutes)
            overlaps = self.search([
                ('id', '!=', rec.id),
                ('doctor_id', '=', rec.doctor_id.id),
                ('date', '<', end_dt),
                ('date', '>=', start_dt - timedelta(minutes=rec.duration_minutes)),
                ('state', '!=', 'cancel'),
            ])
            if overlaps:
                raise ValidationError(f"Doctor {rec.doctor_id.name} already has another visit during this time.")

    @api.onchange('department_id')
    def _onchange_department_id(self):
        for rec in self:
            rec.doctor_id = False

    @api.constrains('insurance_percentage')
    def _check_insurance_percentage(self):
        for rec in self:
            if rec.insurance_percentage < 0 or rec.insurance_percentage > 100:
                raise ValidationError(_("Insurance percentage must be between 0 and 100"))

    # =========================
    # 🔹 ACTIONS
    # =========================
    def action_create_invoice(self):
        for rec in self:
            if rec.invoice_id:
                raise ValidationError(_("Invoice already created for this visit."))

            lines = [
                (0, 0, {
                    'name': f"Medical Visit ({rec.visit_type})",
                    'quantity': 1,
                    'price_unit': rec.total_cost,
                    'currency_id': rec.currency_id.id,
                    'tax_ids': False,
                })
            ]

            if rec.insurance_amount:
                lines.append(
                    (0, 0, {
                        'name': 'Insurance Coverage',
                        'quantity': 1,
                        'price_unit': -rec.insurance_amount,
                        'currency_id': rec.currency_id.id,
                        'tax_ids': False,
                    })
                )

            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': rec.patient_id.partner_id.id,
                'invoice_date': rec.date.date(),
                'invoice_line_ids': lines,
            }

            invoice = self.env['account.move'].create(invoice_vals)

            rec.invoice_id = invoice.id
            rec.state = 'invoiced'

            return {
                'name': _("Invoice"),
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': invoice.id,
                'type': 'ir.actions.act_window',
            }

    def action_done(self):
        for rec in self:
            rec.state = 'done'
            if rec.patient_id:
                p = rec.patient_id
                p.update({
                    'age': rec.age,
                    'gender': rec.gender,
                    'occupation': rec.occupation,
                    'phone_no': rec.phone_no,
                    'address': rec.address,
                    'has_diabetes': rec.has_diabetes,
                    'has_hypertension': rec.has_hypertension,
                    'has_heart_disease': rec.has_heart_disease,
                    'has_kidney_disease': rec.has_kidney_disease,
                    'has_liver_disease': rec.has_liver_disease,
                    'allergies': rec.allergies,
                    'current_medications': rec.current_medications,
                    'previous_surgeries': rec.previous_surgeries,
                    'smoking': rec.smoking,
                    'alcohol': rec.alcohol,
                    'physical_activity_level': rec.physical_activity_level,
                })
                p.medical_visit_ids |= rec

    def action_cancel(self):
        for rec in self:
            if not rec.cancel_reason:
                raise ValidationError("You should enter cancel reason before cancellation")
            # 🧾 1. Reverse Invoice (Credit Note)
            invoice = rec.invoice_id
            if invoice and invoice.state == 'posted':
                reverse_wizard = self.env['account.move.reversal'].create({
                    'move_ids': [(6, 0, invoice.ids)],
                    'reason': 'Cancel Medical Visit',
                    'journal_id': invoice.journal_id.id,
                    'date': fields.Date.today(),
                })
                reverse_result = reverse_wizard.reverse_moves()
                credit_note = self.env['account.move'].browse(reverse_result['res_id'])
                credit_note.action_post()

                # optional: reconcile
                (invoice.line_ids + credit_note.line_ids).filtered(
                    lambda l: l.account_id == invoice.partner_id.property_account_receivable_id
                              and not l.reconciled
                ).reconcile()

            # 💰 2. Reverse Payments
            for payment in rec.advance_payment_ids:
                if payment.state == 'posted' and payment.move_id:
                    reverse_wizard = self.env['account.move.reversal'].create({
                        'move_ids': [(6, 0, payment.move_id.ids)],
                        'reason': f"Refund for {payment.ref}",
                        'journal_id': payment.journal_id.id,
                        'date': fields.Date.today(),
                    })
                    reverse_wizard.reverse_moves()

            # 🔁 3. Update state
            rec.state = 'cancel'

    # =========================
    # 🔹 SMART BUTTONS
    # =========================
    def action_view_advance_payments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Advance Payments',
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.advance_payment_ids.ids)],
            'target': 'current',
            'context': {
                'default_medical_visit_id': self.id,
            },
        }

    def action_view_invoice(self):
        self.ensure_one()
        if not self.invoice_id:
            # لو مفيش فاتورة، اعمل واحدة
            return self.action_create_invoice()
        # لو موجودة فاتورة، افتحها
        return {
            'name': _("Invoice"),
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'type': 'ir.actions.act_window',
        }


