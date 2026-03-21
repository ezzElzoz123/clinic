# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError
import io
import xlsxwriter
import base64
from datetime import datetime


class FinancialReportWizard(models.TransientModel):
    _name = 'financial.report.wizard'
    _description = 'التقرير المالي للعيادة'

    # ── Filters ──
    date_from     = fields.Date(string='من', required=True,
                                default=lambda self: fields.Date.today().replace(day=1))
    date_to       = fields.Date(string='إلى', required=True,
                                default=fields.Date.today)
    doctor_ids    = fields.Many2many('medical.doctor',     string='الأطباء',
                                     help='اتركه فارغاً لاختيار الكل')
    department_ids = fields.Many2many('medical.department', string='الأقسام',
                                      help='اتركه فارغاً لاختيار الكل')
    report_format = fields.Selection(
        [('pdf', 'PDF'), ('xlsx', 'Excel')],
        string='صيغة التقرير', default='pdf', required=True,
    )

    # ── Helpers ──
    def _get_visits(self):
        domain = [
            ('date', '>=', fields.Datetime.from_string(str(self.date_from) + ' 00:00:00')),
            ('date', '<=', fields.Datetime.from_string(str(self.date_to)   + ' 23:59:59')),
            ('state', '!=', 'cancel'),
        ]
        if self.doctor_ids:
            domain.append(('doctor_id', 'in', self.doctor_ids.ids))
        if self.department_ids:
            domain.append(('department_id', 'in', self.department_ids.ids))
        return self.env['medical.visit'].search(domain, order='date asc')

    def _filter_label(self):
        """نص الفلتر للعنوان"""
        doctor_label = '، '.join(self.doctor_ids.mapped('name')) if self.doctor_ids else 'الكل'
        dept_label   = '، '.join(self.department_ids.mapped('name')) if self.department_ids else 'الكل'
        return doctor_label, dept_label

    @staticmethod
    def _invoice_state_ar(visit):
        state_map = {
            'not_paid':         'غير مدفوع',
            'in_payment':       'قيد الدفع',
            'paid':             'مدفوع',
            'partial':          'مدفوع جزئياً',
            'reversed':         'ملغي',
            'invoicing_legacy': 'قديم',
        }
        if not visit.invoice_id:
            return 'لا توجد فاتورة'
        return state_map.get(visit.invoice_state, visit.invoice_state or '—')

    @staticmethod
    def _invoice_state_color(state_ar):
        if state_ar == 'مدفوع':         return 'ok'
        if state_ar == 'غير مدفوع':    return 'out'
        if state_ar == 'مدفوع جزئياً': return 'low'
        return 'neutral'

    # ── Actions ──
    def action_print(self):
        visits = self._get_visits()
        if not visits:
            raise UserError(_('لا توجد زيارات تطابق الفلاتر المحددة'))

        doctor_label, dept_label = self._filter_label()

        if self.report_format == 'pdf':
            return self.env.ref('clinic.action_report_financial').with_context(
                active_ids=visits.ids,
                active_model='medical.visit',
                wizard_date_from=str(self.date_from),
                wizard_date_to=str(self.date_to),
                wizard_doctor=doctor_label,
                wizard_department=dept_label,
            ).report_action(visits)
        else:
            return self._export_xlsx(visits, doctor_label, dept_label)

    # ── Excel ──
    def _export_xlsx(self, visits, doctor_label, dept_label):
        output   = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        teal_dark  = '#1A7A8A'
        teal_mid   = '#2BBCD4'
        teal_light = '#EAF8FB'
        white      = '#FFFFFF'

        def fmt(**kw):
            base = {'font_size': 10, 'valign': 'vcenter', 'border': 1, 'border_color': '#D0EEF4'}
            base.update(kw)
            return workbook.add_format(base)

        fmt_title     = fmt(bold=True, font_size=16, font_color=white,      bg_color=teal_dark,  align='center', border=0)
        fmt_subtitle  = fmt(font_size=10, font_color=white,                 bg_color=teal_mid,   align='center', border=0)
        fmt_hdr       = fmt(bold=True, font_size=10, font_color=white,      bg_color=teal_dark,  align='center', border=1, border_color=teal_mid)
        fmt_sum_lbl   = fmt(bold=True, font_color=teal_dark,                bg_color=teal_light, align='center', border=1, border_color=teal_mid)
        fmt_sum_val   = fmt(bold=True, font_size=13, font_color=teal_dark,  bg_color=white,      align='center', border=1, border_color=teal_mid)
        fmt_sum_money = fmt(bold=True, font_size=12, font_color=teal_dark,  bg_color=white,      align='center', border=1, border_color=teal_mid, num_format='#,##0.00')
        fmt_even      = fmt(bg_color=teal_light)
        fmt_odd       = fmt(bg_color=white)
        fmt_num_even  = fmt(bg_color=teal_light, bold=True, font_color=teal_dark, align='center', num_format='#,##0.00')
        fmt_num_odd   = fmt(bg_color=white,      bold=True, font_color=teal_dark, align='center', num_format='#,##0.00')
        fmt_idx_even  = fmt(bg_color=teal_light, bold=True, font_color=teal_dark, align='center')
        fmt_idx_odd   = fmt(bg_color=white,      bold=True, font_color=teal_dark, align='center')
        fmt_ok        = fmt(bold=True, font_color='#1E8449', bg_color='#D5F5E3', align='center')
        fmt_out       = fmt(bold=True, font_color='#C0392B', bg_color='#FADBD8', align='center')
        fmt_low       = fmt(bold=True, font_color='#CA6F1E', bg_color='#FDEBD0', align='center')
        fmt_neutral   = fmt(font_color='#5A8A95',            bg_color='#F5F5F5', align='center')
        fmt_total_lbl = fmt(bold=True, font_size=11, font_color=white, bg_color=teal_dark, border=1, border_color=teal_mid)
        fmt_total_num = fmt(bold=True, font_size=11, font_color=white, bg_color=teal_dark, border=1, border_color=teal_mid, align='center', num_format='#,##0.00')

        ws = workbook.add_worksheet('التقرير المالي')
        ws.right_to_left()
        ws.set_zoom(85)

        widths = [5, 22, 18, 16, 14, 13, 13, 13, 13, 16]
        for i, w in enumerate(widths):
            ws.set_column(i, i, w)

        # ── Title ──
        ws.set_row(0, 35)
        ws.merge_range('A1:J1', 'ezmedica  |  التقرير المالي للعيادة', fmt_title)
        ws.set_row(1, 20)
        ws.merge_range('A2:J2',
            f'الفترة: {self.date_from.strftime("%d/%m/%Y")} — {self.date_to.strftime("%d/%m/%Y")}'
            f'   |   الأطباء: {doctor_label}   |   الأقسام: {dept_label}',
            fmt_subtitle)

        # ── Summary ──
        total_visits    = len(visits)
        total_revenue   = sum(v.total_cost       for v in visits)
        total_paid      = sum(v.total_cost       for v in visits if v.invoice_state == 'paid')
        total_unpaid    = total_revenue - total_paid
        total_insurance = sum(v.insurance_amount for v in visits)
        total_patient   = sum(v.patient_amount   for v in visits)

        ws.set_row(3, 18); ws.set_row(4, 24)

        ws.merge_range('A4:B4', 'إجمالي الكشوفات',  fmt_sum_lbl)
        ws.merge_range('C4:D4', 'إجمالي الإيرادات', fmt_sum_lbl)
        ws.merge_range('E4:F4', 'مدفوع',             fmt_sum_lbl)
        ws.merge_range('G4:H4', 'غير مدفوع',         fmt_sum_lbl)
        ws.merge_range('I4:J4', 'تأمين',             fmt_sum_lbl)

        ws.merge_range('A5:B5', total_visits,    fmt_sum_val)
        ws.merge_range('C5:D5', total_revenue,   fmt_sum_money)
        ws.merge_range('E5:F5', total_paid,      fmt_sum_money)
        ws.merge_range('G5:H5', total_unpaid,    fmt_sum_money)
        ws.merge_range('I5:J5', total_insurance, fmt_sum_money)

        # ── Table Header ──
        headers = ['م', 'اسم المريض', 'الدكتور', 'القسم', 'تاريخ الكشف',
                   'سعر الكشف', 'الإجمالي', 'التأمين', 'على المريض', 'حالة الفاتورة']
        ws.set_row(7, 22)
        for col, h in enumerate(headers):
            ws.write(7, col, h, fmt_hdr)

        # ── Data ──
        row = 8
        grand_total = grand_insurance = grand_patient = 0
        badge_fmts  = {'ok': fmt_ok, 'out': fmt_out, 'low': fmt_low, 'neutral': fmt_neutral}

        for idx, visit in enumerate(visits):
            is_even = idx % 2 == 0
            rf      = fmt_even     if is_even else fmt_odd
            rf_num  = fmt_num_even if is_even else fmt_num_odd
            rf_idx  = fmt_idx_even if is_even else fmt_idx_odd

            state_ar    = self._invoice_state_ar(visit)
            state_color = self._invoice_state_color(state_ar)
            date_str    = visit.date.strftime('%d/%m/%Y %H:%M') if visit.date else '—'

            grand_total     += visit.total_cost
            grand_insurance += visit.insurance_amount
            grand_patient   += visit.patient_amount

            ws.set_row(row, 18)
            ws.write(row, 0, idx + 1,                                                    rf_idx)
            ws.write(row, 1, visit.patient_id.name or '—',                               rf)
            ws.write(row, 2, visit.doctor_id.name  or '—',                               rf)
            ws.write(row, 3, visit.department_id.name if visit.department_id else '—',   rf)
            ws.write(row, 4, date_str,                                                   rf)
            ws.write(row, 5, visit.price,                                                rf_num)
            ws.write(row, 6, visit.total_cost,                                           rf_num)
            ws.write(row, 7, visit.insurance_amount,                                     rf_num)
            ws.write(row, 8, visit.patient_amount,                                       rf_num)
            ws.write(row, 9, state_ar,                                                   badge_fmts[state_color])
            row += 1

        # ── Grand Total ──
        ws.set_row(row, 24)
        ws.merge_range(row, 0, row, 4, '  ◆  الإجمالي العام', fmt_total_lbl)
        ws.write(row, 5, '',              fmt_total_lbl)
        ws.write(row, 6, grand_total,     fmt_total_num)
        ws.write(row, 7, grand_insurance, fmt_total_num)
        ws.write(row, 8, grand_patient,   fmt_total_num)
        ws.write(row, 9, '',              fmt_total_lbl)

        workbook.close()
        output.seek(0)
        xlsx_data = base64.b64encode(output.read())

        attachment = self.env['ir.attachment'].create({
            'name': f'EzMedica_التقرير_المالي_{datetime.now().strftime("%Y%m%d")}.xlsx',
            'type': 'binary',
            'datas': xlsx_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }