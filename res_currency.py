from odoo import models, fields, api, _
from datetime import datetime, timedelta


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    rate = fields.Float(compute='_compute_current_rate', string='Current Rate', digits=(12, 6),
                        help='The rate of the currency to the currency of rate 1.')

    @api.multi
    @api.depends('rate_ids.rate')
    def _compute_current_rate(self):
        date = self._context.get('date') or fields.Datetime.now()
        company_id = self._context.get('company_id') or self.env['res.users']._get_company().id
        # the subquery selects the last rate before 'date' for the given currency/company
        query = """SELECT c.id, (SELECT r.rate FROM res_currency_rate r
                                      WHERE r.currency_id = c.id AND r.name::DATE <= %s
                                        AND (r.company_id IS NULL OR r.company_id = %s)
                                   ORDER BY r.company_id, r.name DESC
                                      LIMIT 1) AS rate
                       FROM res_currency c
                       WHERE c.id IN %s"""
        self._cr.execute(query, (date, company_id, tuple(self.ids)))
        currency_rates = dict(self._cr.fetchall())
        for currency in self:
            currency.rate = currency_rates.get(currency.id) or 1.0
            # if currency.name == 'BOB':
            #     products = self.env['product.template'].search([('active', '=', True)])
            #     for product in products:
            #         product.list_price_sec = currency.rate * product.list_price

    def update_price_sale(self):
        fecha_hoy = fields.Date.to_string(datetime.now() - timedelta(hours=4))
        #fecha_hoy = fields.Date.to_string(datetime.now())
        currency_id = self.env['res.currency'].search([('name', '=', 'BOB')])
        currency_rate = self.env['res.currency.rate'].search([('currency_id', '=', currency_id[0].id),
                                                              ('name', '>=', str(fecha_hoy) + ' 00:00:00'),
                                                              ('name', '<=', str(fecha_hoy) + ' 23:59:59')])
        if currency_rate:
            rate = currency_rate[0].rate
            products = self.env['product.template'].search([('active', '=', True)])
            for product in products:
                product.list_price_sec = rate * product.list_price


class ResCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    # @api.model
    # def create(self, values):
    #     """ Override to avoid automatic logging of creation """
    #     rate = values.get('rate', False)
    #     result = super(ResCurrencyRate, self).create(values)
    #     if result.currency_id.name == 'BOB':
    #         products = self.env['product.template'].search([('active', '=', True)])
    #         for product in products:
    #             product.list_price_sec = rate * product.list_price
    #     return result

    @api.multi
    def write(self, values):
        rate = values.get('rate', False)
        result = super(ResCurrencyRate, self).write(values)
        if self.currency_id.name == 'BOB':
            fecha_dia = fields.Date.from_string(self.name)
            fecha_hoy = fields.Date.to_string(datetime.now() - timedelta(hours=4))
            if str(fecha_dia) == fecha_hoy:
                products = self.env['product.template'].search([('active', '=', True)])
                for product in products:
                    product.list_price_sec = rate * product.list_price
        return result
