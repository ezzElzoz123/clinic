from odoo import models, fields, api

class MedicalPrescription(models.Model):
    _name = "medical.prescription"
    _description = "Medical Prescription"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string="Medicine", required=True,tracking=True)
    dosage = fields.Char(string="Dosage Instructions", required=True,tracking=True)
    duration = fields.Char(string="Duration",tracking=True)
    note = fields.Text(string="Notes",tracking=True)