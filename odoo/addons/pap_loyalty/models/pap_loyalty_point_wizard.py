# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PapLoyaltyPointWizard(models.TransientModel):
    _name = 'pap.loyalty.point.wizard'
    _description = 'Asistente de Ajuste de Puntos'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Cliente',
        required=True,
        readonly=True,
    )
    points = fields.Integer(
        string='Puntos',
        required=True,
        help='Positivo para añadir, negativo para deducir.',
    )
    notes = fields.Text(string='Notas')

    @api.constrains('points')
    def _check_points_not_zero(self):
        for wizard in self:
            if wizard.points == 0:
                raise ValidationError("El ajuste no puede ser de cero puntos.")

    def action_apply(self):
        self.env['pap.loyalty.move'].create({
            'partner_id': self.partner_id.id,
            'points': self.points,
            'move_type': 'adjust',
            'state': 'done',
            'notes': self.notes,
        })
        return {'type': 'ir.actions.act_window_close'}
