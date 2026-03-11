from odoo import models, fields, api

class MedicalDoctor(models.Model):
    _name = "medical.doctor"
    _description = "Doctor"
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Doctor Name", tracking=True)
    age = fields.Integer(string="Age", tracking=True)
    department_id = fields.Many2one('medical.department', required=True, string="Department", tracking=True)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string="Gender", tracking=True)
    phone_no = fields.Char(
        string="Phone Number",
        help="Enter the doctor's main contact number (e.g. mobile or landline).",
        size=11, tracking=True
    )
    address = fields.Char(
        string="Address",
        help="Enter the doctor's full home address including street and city.", tracking=True
    )
    nat_id = fields.Char(
        string="National Identity",
        help="Enter the doctor's National Identity number",
        size=14, tracking=True
    )
    schedule_ids = fields.One2many(
        "medical.doctor.schedule",
        "doctor_id",
        string="Doctor Schedules"
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string="Related Employee",
        readonly=True,
        tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string="Related Partner",
        readonly=True,
        tracking=True
    )
    details = fields.Text(tracking=True)

    @api.model
    def create(self, vals):
        # 1. create partner
        partner_vals = {
            'name': vals.get('name'),
            'phone': vals.get('phone_no'),
            'street': vals.get('address'),
        }
        partner = self.env['res.partner'].create(partner_vals)

        # 2. create employee
        employee_vals = {
            'name': vals.get('name'),
            'work_contact_id': partner.id,
            'work_phone': vals.get('phone_no'),
            'gender': vals.get('gender'),
            'birthday': vals.get('dob'),
            'identification_id': vals.get('nat_id'),
        }
        employee = self.env['hr.employee'].create(employee_vals)

        # 3. inject employee_id & partner_id into doctor vals
        vals['employee_id'] = employee.id
        vals['partner_id'] = partner.id

        # 4. create doctor
        doctor = super(MedicalDoctor, self).create(vals)
        return doctor

    @api.constrains('name','phone_no','address')
    def edit_partner_details(self):
        for rec in self:
            rec.partner_id.name = rec.name
            rec.employee_id.name = rec.name
            rec.partner_id.phone = rec.phone_no
            rec.employee_id.work_phone = rec.phone_no
            rec.partner_id.street = rec.address