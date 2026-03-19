{
    'name': 'Clinic',
    'summary': 'Medical Branch',
    'author': "Ezzeldin",
    'version': '16.0.0.1.0',
    'category': 'Technical',
    'license': 'AGPL-3',
    'sequence': 1,
    'depends': [
        'base', 'base_setup', 'purchase', 'account_accountant', 'hr', 'sale_management', 'stock', 'web'
    ],
    # موديول المحاسبة هنزل اخوه الكوميونتي من اودو ابس علشان يشتغل كوميونتي
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/cron.xml',
        'wizard/payment_wizard_view.xml',
        'views/res_config_settings_view.xml',
        'views/medical_visit_view.xml',
        'views/medical_department_view.xml',
        'views/medical_doctor_view.xml',
        'views/medical_patient_view.xml',
        'views/medical_prescription_view.xml',
        'views/account_move_view.xml',
        'views/insurance_company.xml',
        # 'views/dashboard_templates.xml',
        'views/menu_items.xml',
        'report/paper_fromat.xml',
        'report/prescription_view.xml',
        'report/medical_report.xml',
        'report/medical_invoice_view.xml',
        'report/report_action_view.xml',
    ],
    'demo': [
        # 'demo/',
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'clinic/static/src/scss/clinic_theme.scss',
    #         'clinic/static/src/js/dark_mode_toggle.js',
    #         'clinic/static/src/js/clinic_side_bar.js',
    #         'clinic/static/src/xml/dark_mode_toggle.xml',
    #         'clinic/static/src/xml/clinic_sidebar.xml',
    #     ],
    # },
    'installable': True,
    'application': True,
    'auto_install': False,
}
