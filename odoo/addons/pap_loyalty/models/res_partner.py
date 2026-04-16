# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    loyalty_points = fields.Integer(
        string='Loyalty Points',
        compute='_compute_loyalty_points',
        store=True,
    )
    commercial_consent = fields.Boolean(
        string='Commercial Consent',
        default=False,
    )
    loyalty_move_ids = fields.One2many(
        comodel_name='pap.loyalty.move',
        inverse_name='partner_id',
        string='Loyalty History',
    )

    @api.depends('loyalty_move_ids.points', 'loyalty_move_ids.state')
    def _compute_loyalty_points(self):
        for partner in self:
            partner.loyalty_points = sum(
                move.points
                for move in partner.loyalty_move_ids
                if move.state == 'done'
            )
