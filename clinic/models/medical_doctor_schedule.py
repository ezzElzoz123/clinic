from odoo import models, fields

class MedicalDoctorSchedule(models.Model):
    _name = "medical.doctor.schedule"
    _description = "Doctor Schedule"
    _order = "day_of_week, start_time"

    doctor_id = fields.Many2one(
        "medical.doctor",
        string="Doctor",
        required=True,
        ondelete="cascade"
    )
    day_of_week = fields.Selection([
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
    ], string="Day of Week", required=True)

    start_time = fields.Float(string="Start Time", required=True,
                              help="Start hour in 24h format, e.g. 9.0 = 09:00 AM")
    end_time = fields.Float(string="End Time", required=True,
                            help="End hour in 24h format, e.g. 17.5 = 05:30 PM")
