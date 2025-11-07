from odoo import models, fields, api

class MedicalPatient(models.Model):
    _name = "medical.patient"
    _description = "Patient"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Full Name", required=True, tracking=True)
    age = fields.Integer(string="Age", tracking=True)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string="Gender")
    occupation = fields.Char(string="Occupation", tracking=True)
    phone_no = fields.Char(string="Phone Number", tracking=True)
    address = fields.Char(string="Address", tracking=True)
    partner_id = fields.Many2one('res.partner', string="Related Partner", readonly=True, tracking=True)

    # Chronic Diseases
    has_diabetes = fields.Boolean(string="Diabetes", tracking=True)
    has_hypertension = fields.Boolean(string="Hypertension", tracking=True)
    has_heart_disease = fields.Boolean(string="Heart Disease", tracking=True)
    has_kidney_disease = fields.Boolean(string="Kidney Disease", tracking=True)
    has_liver_disease = fields.Boolean(string="Liver Disease", tracking=True)

    # Other Info
    allergies = fields.Text(string="Allergies", tracking=True)
    current_medications = fields.Text(string="Current Medications", tracking=True)
    previous_surgeries = fields.Text(string="Previous Surgeries", tracking=True)

    # Lifestyle
    smoking = fields.Boolean(string="Smoker", tracking=True)
    alcohol = fields.Boolean(string="Alcohol Consumption", tracking=True)
    physical_activity_level = fields.Selection([
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
    ], string="Physical Activity Level", tracking=True)
    medical_visit_ids=fields.One2many('medical.visit','patient_id')

    @api.model
    def create(self, vals):
        # create the partner first
        partner_vals = {
            'name': vals.get('name'),
            'phone': vals.get('phone_no'),
            'street': vals.get('address'),
        }
        partner = self.env['res.partner'].create(partner_vals)

        # inject partner_id into patient vals
        vals['partner_id'] = partner.id

        # create the patient
        patient = super(MedicalPatient, self).create(vals)
        return patient

    @api.constrains('name','phone_no','address')
    def edit_partner_details(self):
        for rec in self:
            rec.partner_id.name = rec.name
            rec.partner_id.phone = rec.phone_no
            rec.partner_id.street = rec.address

    def action_open_medical_visits(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Medical Visits',
            'res_model': 'medical.visit',
            'view_mode': 'tree,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }

