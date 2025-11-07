from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    checkup_price = fields.Float(string="Default Checkup Price", default=300, config_parameter='clinic_test.checkup_price')
    consultation_price = fields.Float(string="Default Consultation Price", default=150, config_parameter='clinic_test.consultation_price')
