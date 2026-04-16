# -*- coding: utf-8 -*-
{
    'name': 'Papelería El Estudiante - Loyalty',
    'version': '17.0.1.0.0',
    'summary': 'Loyalty and base configuration for Papelería El Estudiante',
    'description': """
        Base module for Papelería El Estudiante digitalization project.
        Provides demo data, product catalog, and customer base setup.
    """,
    'author': 'Papelería El Estudiante',
    'category': 'Sales/Point of Sale',
    'depends': [
        'base',
        'sale_management',
        'point_of_sale',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/pap_loyalty_move_views.xml',
        'views/res_partner_views.xml',
        'views/product_template_views.xml',
        'data/demo.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
