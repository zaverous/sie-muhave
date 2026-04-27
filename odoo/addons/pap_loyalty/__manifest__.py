# -*- coding: utf-8 -*-
{
    'name': 'Papelería El Estudiante - Fidelización',
    'version': '17.0.1.0.0',
    'summary': 'Fidelización y configuración base para Papelería El Estudiante',
    'description': """
        Módulo base del proyecto de digitalización de Papelería El Estudiante.
        Incluye datos de demostración, catálogo de productos y configuración de clientes.
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
        'views/pap_loyalty_point_wizard_views.xml',
        'views/res_partner_views.xml',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'data/demo.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
