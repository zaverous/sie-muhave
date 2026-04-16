# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PapLoyaltyMove(models.Model):
    _name = 'pap.loyalty.move'
    _description = 'Loyalty Points Move'
    _order = 'date desc, id desc'

    reference = fields.Char(
        string='Reference',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        required=True,
        ondelete='restrict',
    )
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        ondelete='set null',
    )
    date = fields.Datetime(
        string='Date',
        default=fields.Datetime.now,
    )
    points = fields.Integer(
        string='Points',
    )
    move_type = fields.Selection(
        selection=[
            ('earn', 'Earn'),
            ('redeem', 'Redeem'),
            ('adjust', 'Adjust'),
        ],
        string='Type',
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
    )
    notes = fields.Text(
        string='Notes',
    )

    @api.constrains('points')
    def _check_points_not_zero(self):
        for move in self:
            if move.points == 0:
                raise ValidationError("A loyalty move cannot have zero points.")
