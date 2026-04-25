# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    loyalty_eligible = fields.Boolean(
        string='Apto para Fidelización',
        default=False,
    )
    redeemable = fields.Boolean(
        string='Canjeable con Puntos',
        default=False,
    )
    loyalty_ratio = fields.Float(
        string='Ratio de Fidelización (pts/€)',
        default=0.0,
        digits=(16, 4),
    )
    loyalty_cost = fields.Integer(
        string='Coste en Puntos',
        default=0,
    )
