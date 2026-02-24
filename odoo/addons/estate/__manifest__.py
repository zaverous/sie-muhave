{
    'name': 'Real Estate',
    'version': '1.0',
    'summary': 'Real Estate Module',
    'description': 'A module to manage real estate properties',
    'category': 'Real Estate',
    'author': 'Author Name',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/estate_property_views.xml',
        'views/estate_menus.xml',
    ],
    'installable': True,
    'application': True,
}