# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
import odoo.addons.decimal_precision as dp


class ProductProduct(models.Model):
    _inherit = 'product.product'

    lst_price_sec = fields.Float(
        'Precio Venta Bs.', compute='_compute_product_lst_price_sec',
        digits=dp.get_precision('Product Price'), inverse='_set_product_lst_price_sec',
        help="The sale price is managed from the product template. Click on the 'Variant Prices' button to set the extra attribute prices.")

    @api.depends('list_price_sec')
    def _compute_product_lst_price_sec(self):
        to_uom = None
        if 'uom' in self._context:
            to_uom = self.env['product.uom'].browse([self._context['uom']])

        for product in self:
            if to_uom:
                list_price_sec = product.uom_id._compute_price(product.list_price_sec, to_uom)
            else:
                list_price_sec = product.list_price_sec
            product.lst_price_sec = list_price_sec

    def _set_product_lst_price_sec(self):
        for product in self:
            if self._context.get('uom'):
                value = self.env['product.uom'].browse(self._context['uom'])._compute_price(product.lst_price, product.uom_id)
            else:
                value = product.lst_price_sec
            product.write({'list_price_sec': value})

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    list_price_sec = fields.Float(
        'Precio Venta Bs.', default=1.0,
        digits=dp.get_precision('Product Price'),
        help="Base price to compute the customer price. Sometimes called the catalog price.")
    lst_price_sec = fields.Float(
        'Precio Venta Bs.', related='list_price_sec',
        digits=dp.get_precision('Product Price'))
