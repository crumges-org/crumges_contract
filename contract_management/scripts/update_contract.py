with open("models/contract.py") as f:
    lines = f.readlines()

new_method = """
    @api.model
    def get_global_dashboard_stats(self):
        from datetime import timedelta
        active_contracts = self.search([('state', '=', 'in_progress')])
        expiring_domain = [
            ('state', '=', 'in_progress'),
            ('date_end', '!=', False),
            ('date_end', '<=', fields.Date.today() + timedelta(days=30))
        ]
        expiring = self.search_count(expiring_domain)

        total_revenue = 0
        company_currency = self.env.company.currency_id
        for contract in active_contracts:
            amount = sum(contract.contract_line_ids.mapped('price_subtotal'))
            if contract.currency_id and company_currency and contract.currency_id != company_currency:
                amount = contract.currency_id._convert(amount, company_currency, self.env.company, fields.Date.today())
            total_revenue += amount

        return {
            'total_active': len(active_contracts),
            'total_revenue': round(total_revenue, 2),
            'expiring_soon': expiring,
            'currency_symbol': company_currency.symbol or '$',
        }
"""

lines.append(new_method)
with open("models/contract.py", "w") as f:
    f.writelines(lines)
