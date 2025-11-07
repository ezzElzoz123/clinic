from odoo import fields, models, api


class MedicalDepartment(models.Model):
    _name = "medical.department"
    _description = "Medical Department"
    _rec_name = "name"
    _order = "name"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Department Name", required=True, tracking=True)
    code = fields.Char(string="Code", readonly=True, copy=False, index=True)
    description = fields.Text(string="Description", tracking=True)
    doctor_ids = fields.One2many(
        "medical.doctor",
        "department_id",
        string="Doctors", tracking=True
    )
    visit_ids = fields.One2many(
        "medical.visit",
        "department_id",
        string="Medical Visits", tracking=True
    )

    @api.model
    def create(self, vals):
        if not vals.get("code"):
            vals["code"] = self.env["ir.sequence"].next_by_code("medical.department") or "NEW"
        return super(MedicalDepartment, self).create(vals)
