# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError
import io
import xlsxwriter
import base64
from datetime import datetime


class ProductStockReportWizard(models.TransientModel):
    _name = 'product.stock.report.wizard'
    _description = 'تقرير المخزون'

    only_available = fields.Boolean(
        string='المتوفر فقط',
        default=False,
        help='يظهر المنتجات المتوفرة فقط'
    )
    report_format = fields.Selection(
        [('pdf', 'PDF'), ('xlsx', 'Excel')],
        string='صيغة التقرير',
        default='pdf',
        required=True,
    )

    def _get_products(self):
        domain = [('type', '=', 'consu')]
        if self.only_available:
            domain.append(('qty_available', '>', 0))
        return self.env['product.product'].search(domain, order='name')

    def action_print(self):
        products = self._get_products()
        if not products:
            raise UserError(_('لا توجد منتجات قابلة للاستهلاك تطابق الفلاتر المحددة'))

        if self.report_format == 'pdf':
            return self.env.ref(
                'clinic.action_report_ezmedica_product_stock'
            ).with_context(
                active_ids=products.ids,
                active_model='product.product',
            ).report_action(products)
        else:
            return self._export_xlsx(products)

    def _export_xlsx(self, products):
        output   = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        teal_dark  = '#1A7A8A'
        teal_mid   = '#2BBCD4'
        teal_light = '#EAF8FB'
        white      = '#FFFFFF'

        fmt_title = workbook.add_format({
            'bold': True, 'font_size': 16,
            'font_color': white, 'bg_color': teal_dark,
            'align': 'center', 'valign': 'vcenter',
        })
        fmt_subtitle = workbook.add_format({
            'font_size': 10, 'font_color': white,
            'bg_color': teal_mid, 'align': 'center',
        })
        fmt_header = workbook.add_format({
            'bold': True, 'font_size': 10,
            'font_color': white, 'bg_color': teal_dark,
            'align': 'center', 'valign': 'vcenter',
            'border': 1, 'border_color': teal_mid,
        })
        fmt_even = workbook.add_format({
            'font_size': 10, 'bg_color': teal_light,
            'border': 1, 'border_color': '#D0EEF4',
            'valign': 'vcenter',
        })
        fmt_odd = workbook.add_format({
            'font_size': 10, 'bg_color': white,
            'border': 1, 'border_color': '#D0EEF4',
            'valign': 'vcenter',
        })
        fmt_num_even = workbook.add_format({
            'font_size': 11, 'bg_color': teal_light,
            'border': 1, 'border_color': '#D0EEF4',
            'num_format': '#,##0', 'align': 'center',
            'bold': True, 'font_color': teal_dark,
        })
        fmt_num_odd = workbook.add_format({
            'font_size': 11, 'bg_color': white,
            'border': 1, 'border_color': '#D0EEF4',
            'num_format': '#,##0', 'align': 'center',
            'bold': True, 'font_color': teal_dark,
        })
        fmt_badge_ok = workbook.add_format({
            'font_size': 9, 'bold': True,
            'font_color': '#1E8449', 'bg_color': '#D5F5E3',
            'border': 1, 'border_color': '#A9DFBF', 'align': 'center',
        })
        fmt_badge_low = workbook.add_format({
            'font_size': 9, 'bold': True,
            'font_color': '#CA6F1E', 'bg_color': '#FDEBD0',
            'border': 1, 'border_color': '#F5CBA7', 'align': 'center',
        })
        fmt_badge_out = workbook.add_format({
            'font_size': 9, 'bold': True,
            'font_color': '#C0392B', 'bg_color': '#FADBD8',
            'border': 1, 'border_color': '#F1948A', 'align': 'center',
        })
        fmt_total_label = workbook.add_format({
            'bold': True, 'font_size': 11,
            'font_color': white, 'bg_color': teal_dark,
            'border': 1, 'border_color': teal_mid,
        })
        fmt_total_num = workbook.add_format({
            'bold': True, 'font_size': 11,
            'font_color': white, 'bg_color': teal_dark,
            'border': 1, 'border_color': teal_mid,
            'num_format': '#,##0', 'align': 'center',
        })
        fmt_sum_label = workbook.add_format({
            'bold': True, 'font_size': 10,
            'font_color': teal_dark, 'bg_color': teal_light,
            'border': 1, 'border_color': teal_mid, 'align': 'center',
        })
        fmt_sum_val = workbook.add_format({
            'bold': True, 'font_size': 13,
            'font_color': teal_dark, 'bg_color': white,
            'border': 1, 'border_color': teal_mid, 'align': 'center',
        })

        ws = workbook.add_worksheet('تقرير المخزون')
        ws.right_to_left()
        ws.set_zoom(90)

        ws.set_column(0, 0, 6)   # م
        ws.set_column(1, 1, 40)  # اسم المنتج
        ws.set_column(2, 2, 15)  # الكمية المتاحة
        ws.set_column(3, 3, 14)  # الوحدة
        ws.set_column(4, 4, 16)  # الحالة

        # ── Title ──
        ws.set_row(0, 35)
        ws.merge_range('A1:E1', 'ezmedica  |  تقرير المخزون', fmt_title)
        ws.set_row(1, 20)
        ws.merge_range('A2:E2',
            'تاريخ الطباعة: ' + datetime.now().strftime('%d/%m/%Y %H:%M') +
            '   |   نظام إدارة العيادات',
            fmt_subtitle
        )

        # ── Summary ──
        total     = len(products)
        out       = len(products.filtered(lambda p: p.qty_available <= 0))
        low       = len(products.filtered(lambda p: 0 < p.qty_available <= 5))
        ok        = total - out - low
        total_qty = sum(p.qty_available for p in products)

        ws.set_row(3, 18)
        ws.set_row(4, 24)
        ws.write('B4', 'إجمالي المنتجات', fmt_sum_label)
        ws.write('C4', 'متوفر',           fmt_sum_label)
        ws.write('D4', 'مخزون منخفض',     fmt_sum_label)
        ws.write('E4', 'نفد المخزون',      fmt_sum_label)
        ws.write('B5', total, fmt_sum_val)
        ws.write('C5', ok,    fmt_sum_val)
        ws.write('D5', low,   fmt_sum_val)
        ws.write('E5', out,   fmt_sum_val)

        # ── Table Header ──
        headers = ['م', 'اسم المنتج', 'الكمية المتاحة', 'الوحدة', 'الحالة']
        ws.set_row(6, 22)
        for col, h in enumerate(headers):
            ws.write(6, col, h, fmt_header)

        # ── Data (flat - no grouping) ──
        row       = 7
        grand_qty = 0

        for idx, product in enumerate(products):
            is_even  = idx % 2 == 0
            rf       = fmt_even     if is_even else fmt_odd
            rf_num   = fmt_num_even if is_even else fmt_num_odd

            qty        = product.qty_available
            grand_qty += qty

            if qty <= 0:
                badge_fmt, badge_txt = fmt_badge_out, 'نفد المخزون'
            elif qty <= 5:
                badge_fmt, badge_txt = fmt_badge_low, 'مخزون منخفض'
            else:
                badge_fmt, badge_txt = fmt_badge_ok,  'متوفر'

            ws.set_row(row, 18)
            ws.write(row, 0, idx + 1,            rf_num)
            ws.write(row, 1, product.name,        rf)
            ws.write(row, 2, qty,                 rf_num)
            ws.write(row, 3, product.uom_id.name, rf)
            ws.write(row, 4, badge_txt,           badge_fmt)
            row += 1

        # ── Grand Total ──
        # row += 1
        ws.set_row(row, 24)
        ws.merge_range(row, 0, row, 1, '  ◆  الإجمالي العام', fmt_total_label)
        ws.write(row, 2, grand_qty, fmt_total_num)
        ws.write(row, 3, '',        fmt_total_label)
        ws.write(row, 4, '',        fmt_total_label)

        workbook.close()
        output.seek(0)
        xlsx_data = base64.b64encode(output.read())

        attachment = self.env['ir.attachment'].create({
            'name': 'EzMedica_تقرير_المخزون.xlsx',
            'type': 'binary',
            'datas': xlsx_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }