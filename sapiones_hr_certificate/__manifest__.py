{
    'name': 'Employee Certificates & Expiry Alerts',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Track employee certificates, licenses & qualifications with automatic expiry reminders',
    'description': """
Employee Certificates & Expiry Alerts
=====================================

Keep every employee certificate, licence and qualification in one place —
and never miss a renewal again.

* Certificate registry per employee: number, issuing body, issue/expiry dates, attached file
* Configurable certificate types (safety, equipment operation, professional, language, degree…)
  with a default validity period and a "mandatory" flag
* Automatic status — Valid / Expiring soon / Expired / No expiry — with days to expiry
* Scheduled reminder auto-creates a to-do activity for the manager before a certificate expires
* Certificates tab on the employee form, an alert flag, and filtered reporting

Depends only on standard Odoo HR (``hr``). Free & open source (LGPL-3).

Developed by BSD — https://bsdinsight.com
""",
    'author': 'BSD',
    'website': 'https://bsdinsight.com',
    'support': 'info@bsdinsight.com',
    'license': 'LGPL-3',
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/certificate_type_data.xml',
        'data/cron_data.xml',
        'views/certificate_views.xml',
        'views/hr_employee_views.xml',
        'views/menus.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
}
