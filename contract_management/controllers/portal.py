from odoo import http
from odoo.http import request
from odoo.osv import expression
from odoo.addons.portal.controllers.portal import CustomerPortal

class ContractManagementCustomerPortal(CustomerPortal):

    def _get_invoices_domain(self, *args, **kwargs):
        domain = super()._get_invoices_domain(*args, **kwargs) if hasattr(super(), '_get_invoices_domain') else []
        contract_id = request.params.get('contract_id')
        if contract_id:
            try:
                domain = expression.AND([
                    domain, 
                    [('invoice_line_ids.contract_line_id.contract_id', '=', int(contract_id))]
                ])
            except ValueError:
                pass
        return domain

    def _prepare_orders_domain(self, partner, *args, **kwargs):
        domain = super()._prepare_orders_domain(partner, *args, **kwargs) if hasattr(super(), '_prepare_orders_domain') else []
        contract_id = request.params.get('contract_id')
        if contract_id:
            try:
                domain = expression.AND([
                    domain, 
                    [('order_line.contract_line_id.contract_id', '=', int(contract_id))]
                ])
            except ValueError:
                pass
        return domain

    def _prepare_quotations_domain(self, partner, *args, **kwargs):
        domain = super()._prepare_quotations_domain(partner, *args, **kwargs) if hasattr(super(), '_prepare_quotations_domain') else []
        contract_id = request.params.get('contract_id')
        if contract_id:
            try:
                domain = expression.AND([
                    domain, 
                    [('order_line.contract_line_id.contract_id', '=', int(contract_id))]
                ])
            except ValueError:
                pass
        return domain

    def _prepare_my_invoices_values(self, page, date_begin, date_end, sortby, filterby, domain=None, url="/my/invoices"):
        values = {}
        if hasattr(super(), '_prepare_my_invoices_values'):
            values = super()._prepare_my_invoices_values(page, date_begin, date_end, sortby, filterby, domain=domain, url=url)
        contract_id = request.params.get('contract_id')
        if contract_id and 'pager' in values and 'url' in values['pager']:
            try:
                values['pager']['url'] += f"?contract_id={int(contract_id)}"
            except ValueError:
                pass
        return values

    def _prepare_sale_portal_rendering_values(self, page=1, date_begin=None, date_end=None, sortby=None, quotation_page=False, **kwargs):
        values = {}
        if hasattr(super(), '_prepare_sale_portal_rendering_values'):
            values = super()._prepare_sale_portal_rendering_values(page, date_begin, date_end, sortby, quotation_page, **kwargs)
        contract_id = request.params.get('contract_id')
        if contract_id and 'pager' in values and 'url' in values['pager']:
            try:
                values['pager']['url'] += f"?contract_id={int(contract_id)}"
            except ValueError:
                pass
        return values
