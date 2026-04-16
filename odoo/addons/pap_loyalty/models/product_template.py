# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    loyalty_eligible = fields.Boolean(
        string='Earns Loyalty Points',
        default=False,
    )
    redeemable = fields.Boolean(
        string='Redeemable with Points',
        default=False,
    )
    loyalty_ratio = fields.Float(
        string='Loyalty Ratio (pts/€)',
        default=0.0,
        digits=(16, 4),
    )
