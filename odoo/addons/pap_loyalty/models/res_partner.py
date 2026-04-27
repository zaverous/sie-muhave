# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    loyalty_points = fields.Integer(
        string='Puntos de Fidelización',
        compute='_compute_loyalty_points',
        store=True,
    )
    commercial_consent = fields.Boolean(
        string='Consentimiento Comercial',
        default=False,
    )
    loyalty_move_ids = fields.One2many(
        comodel_name='pap.loyalty.move',
        inverse_name='partner_id',
        string='Historial de Fidelización',
    )

    @api.depends('loyalty_move_ids.points', 'loyalty_move_ids.state')
    def _compute_loyalty_points(self):
        for partner in self:
            partner.loyalty_points = sum(
                move.points
                for move in partner.loyalty_move_ids
                if move.state == 'done'
            )

    def action_open_loyalty_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ajuste de Puntos',
            'res_model': 'pap.loyalty.point.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_partner_id': self.id},
        }
