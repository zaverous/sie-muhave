# -*- coding: utf-8 -*-

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_tipo_operacion = fields.Selection(
        selection=[
            ('venta_directa', 'Venta Directa'),
            ('encargo', 'Encargo Complejo'),
        ],
        string='Tipo de Operación',
        default='venta_directa',
        required=True,
    )
