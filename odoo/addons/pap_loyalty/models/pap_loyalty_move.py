# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PapLoyaltyMove(models.Model):
    _name = 'pap.loyalty.move'
    _description = 'Movimiento de Puntos de Fidelización'
    _order = 'date desc, id desc'

    reference = fields.Char(
        string='Referencia',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Cliente',
        required=True,
        ondelete='restrict',
    )
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Pedido de Venta',
        ondelete='set null',
    )
    date = fields.Datetime(
        string='Fecha',
        default=fields.Datetime.now,
    )
    points = fields.Integer(
        string='Puntos',
    )
    move_type = fields.Selection(
        selection=[
            ('earn', 'Acumular'),
            ('redeem', 'Canjear'),
            ('adjust', 'Ajuste'),
        ],
        string='Tipo',
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Borrador'),
            ('done', 'Confirmado'),
            ('cancelled', 'Cancelado'),
        ],
        string='Estado',
        default='draft',
    )
    notes = fields.Text(
        string='Notas',
    )

    @api.constrains('points')
    def _check_points_not_zero(self):
        for move in self:
            if move.points == 0:
                raise ValidationError("Un movimiento de fidelización no puede tener cero puntos.")
