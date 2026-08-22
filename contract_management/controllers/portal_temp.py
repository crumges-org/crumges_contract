from odoo.http import request

from odoo.addons.account.controllers.portal import (
    CustomerPortal as AccountCustomerPortal,
)


class ContractManagementAccountPortal(AccountCustomerPortal):
    def _prepare_my_invoices_values(
        self,
        page,
        date_begin,
        date_end,
        sortby,
        filterby,
        domain=None,
        url="/my/invoices",
    ):
        values = super()._prepare_my_invoices_values(
            page, date_begin, date_end, sortby, filterby, domain, url
        )

        contract_id = request.params.get("contract_id")
        if contract_id:
            try:
                contract_id = int(contract_id)
                # Odoo's default account controller creates 'invoices' as a lambda in values,
                # but it uses the domain evaluated inside `_prepare_my_invoices_values`.
                # Wait, if we call super() first, the domain is already used to fetch search count!
                # We must intercept BEFORE super() to inject the domain.
            except ValueError:
                pass
        return values
