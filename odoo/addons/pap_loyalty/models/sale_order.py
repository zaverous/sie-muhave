# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_tipo_operacion = fields.Selection(
        selection=[
            ('venta_directa', 'Venta Directa'),
            ('encargo', 'Encargo Complejo'),
            ('canje_puntos', 'Canje por Puntos'),
        ],
        string='Tipo de Operación',
        default='venta_directa',
        required=True,
    )
    x_puntos_disponibles = fields.Integer(
        string='Puntos Disponibles',
        related='partner_id.loyalty_points',
        readonly=True,
    )
    x_puntos_requeridos = fields.Integer(
        string='Puntos Requeridos',
        compute='_compute_x_puntos_requeridos',
    )
    x_puntos_suficientes = fields.Boolean(
        string='Puntos Suficientes',
        compute='_compute_x_puntos_suficientes',
    )

    @api.depends('order_line.product_id', 'order_line.product_uom_qty')
    def _compute_x_puntos_requeridos(self):
        for order in self:
            order.x_puntos_requeridos = sum(
                int(line.product_uom_qty) * line.product_id.loyalty_cost
                for line in order.order_line
                if line.product_id.redeemable
            )

    @api.depends('x_puntos_disponibles', 'x_puntos_requeridos')
    def _compute_x_puntos_suficientes(self):
        for order in self:
            order.x_puntos_suficientes = (
                order.x_puntos_requeridos > 0
                and order.x_puntos_disponibles >= order.x_puntos_requeridos
            )

    def action_confirm(self):
        redemptions = {}
        for order in self:
            if order.x_tipo_operacion != 'canje_puntos':
                continue
            if not order.partner_id:
                raise UserError("Selecciona un cliente para canjear puntos.")
            if order.x_puntos_requeridos == 0:
                raise UserError("Ninguna línea del pedido contiene productos canjeables con puntos.")
            if not order.x_puntos_suficientes:
                raise UserError(
                    f"Puntos insuficientes. Disponibles: {order.x_puntos_disponibles}, "
                    f"Requeridos: {order.x_puntos_requeridos}."
                )
            # Capture points before confirm mutates anything
            redemptions[order.id] = order.x_puntos_requeridos
            # Apply 100% discount on redeemable lines so the sale nets to zero
            for line in order.order_line:
                if line.product_id.redeemable:
                    line.discount = 100.0

        result = super().action_confirm()

        for order in self:
            puntos = redemptions.get(order.id)
            if not puntos:
                continue
            self.env['pap.loyalty.move'].create({
                'partner_id': order.partner_id.id,
                'sale_order_id': order.id,
                'points': -puntos,
                'move_type': 'redeem',
                'state': 'done',
                'reference': order.name,
                'notes': f'Canje por pedido {order.name}',
            })

        return result
