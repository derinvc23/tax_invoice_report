# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Treesa Maria Jude(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields, models,api, _


class Invoicelinecount(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def get_count_as(self):
        for inv in self:
            inv.count_line = len(inv.invoice_line_ids)
            inv.count_line1 = len(inv.invoice_line_ids)
            inv.write({'count_line1': len(inv.invoice_line_ids)})

    @api.multi
    def _write(self, vals):
        for i in self:
            vals.update({'count_line1': len(i.invoice_line_ids)})
        pre_not_reconciled = self.filtered(lambda invoice: not invoice.reconciled)
        pre_reconciled = self - pre_not_reconciled
        res = super(Invoicelinecount, self)._write(vals)
        reconciled = self.filtered(lambda invoice: invoice.reconciled)
        not_reconciled = self - reconciled
        (reconciled & pre_reconciled).filtered(lambda invoice: invoice.state == 'open').action_invoice_paid()
        (not_reconciled & pre_not_reconciled).filtered(lambda invoice: invoice.state == 'paid').action_invoice_re_open()
        return res

    count_line = fields.Integer(string="Count", compute="get_count_as", store=False)
    count_line1 = fields.Integer(string="Count1", default=1)

class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    amount_taxes = fields.Float(string='Impuestos', readonly=True)
    amount_totals = fields.Float(string='Total con Impuestos', readonly=True)
    number = fields.Char(string='Nro Factura')
#    brand_name = fields.Char(string='Marca de producto', readonly=True)
#    product_brand_id = fields.Many2one('product.brand', string='Marca de producto', readonly=True)

#    _depends = {
#        'product.brand':['name'],
#    }

    raw_value = fields.Many2one('product.category', string='Categoria Padre', compute='_get_parent_category', store=True)

    @api.depends('categ_id')
    def _get_parent_category(self):
        for record in self:
            record.raw_value = self.get_base_parent(record.categ_id)

    def get_base_parent(self, categ_id):
        if not categ_id.parent_id:
            return categ_id.id
        else:
            return self.get_base_parent(categ_id.parent_id)

    def _select(self):
        return super(AccountInvoiceReport, self)._select() \
               + ", sub.amount_taxes as amount_taxes, sub.amount_totals as amount_totals, sub.number"

    def _sub_select(self):
        return super(AccountInvoiceReport, self)._sub_select() \
               + ",((ai.amount_tax)*(1)) AS amount_taxes, " \
                 " ((ail.price_unit * ail.quantity)-(((ail.price_unit * ail.quantity) * ail.discount) / 100)) as amount_totals, ai.number"
#    def _sub_select(self):
#       return super(AccountInvoiceReport, self)._sub_select() \
#             + ",((ai.amount_tax)*(1)) AS amount_taxes, " \
#              "(ail.price_unit)*(ail.quantity) as amount_totals ,ai.number"

    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + ", ai.number"
