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

from odoo import fields, models, api, _


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
    costo = fields.Float(string='Costo de Venta', readonly=True)
    cantidad_actual = fields.Float(string='Stock Actual', readonly=True)

    def _select(self):
        return super(AccountInvoiceReport, self)._select() \
               + ", sub.amount_taxes as amount_taxes, sub.amount_totals as amount_totals, sub.number, sub.costo, sub.cantidad_actual"

    def _sub_select(self):
        return super(AccountInvoiceReport, self)._sub_select() \
               + """,CASE WHEN t0.tax_id is not null then
                        sum(((ail.price_unit * ail.quantity) - (invoice_type.sign::numeric * ail.quantity/(u.factor * u2.factor)*ail.price_unit * ail.discount/100::numeric))*0.13)
                    ELSE
                        0
                    END AS amount_taxes
                    ,((ail.price_unit * ail.quantity)-(((ail.price_unit * ail.quantity) * ail.discount) / 100)) as amount_totals, ai.number,
                    sum(s1.total)                                                                       as costo,
                    sum(sq.total_qty)                                                                   as cantidad_actual
                    """

    def _from(self):
        res = super(AccountInvoiceReport, self)._from()
        return res + """
        left join account_invoice_line_tax t0 on t0.invoice_line_id = ail.id
        left join (select foo.origin, foo.product_id, sum(foo.total) as total
                          from (
                                   select sm.product_id,
                                          sm.origin,
                                          sm.product_uom_qty,
                                          sm.price_unit,
                                          (sm.product_uom_qty * sm.price_unit) as total
                                   from stock_move sm
                                   where sm.state in ('done')
                               ) as foo
                          group by foo.origin, foo.product_id
                          order by foo.origin) as s1 on s1.product_id = ail.product_id and s1.origin = ai.origin
        left join (select sq.product_id,
                         sum(sq.qty) as total_qty
                  from stock_quant sq
                           inner join stock_location sl on sq.location_id = sl.id
                  where sl.usage in ('internal')
                  group by sq.product_id
                  order by sq.product_id) as sq on sq.product_id = ail.product_id
        """


    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + ", ai.number, t0.tax_id"
