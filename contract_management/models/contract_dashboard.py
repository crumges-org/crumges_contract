from odoo import models, fields, api
import json

class ContractDashboardCard(models.Model):
    _name = 'contract.dashboard.card'
    _description = 'Contract Dashboard Card'

    name = fields.Char(string="Name", required=True, translate=True)
    code = fields.Selection([
        ('sale_invoice', 'Contratos de facturas de venta'),
        ('purchase_invoice', 'Contratos de facturas de compra'),
        ('sale_order', 'Contratos de venta')
    ], string="Type", required=True)
    color = fields.Integer(string="Color Index")
    active = fields.Boolean(default=True)
    
    has_contracts = fields.Boolean(compute='_compute_kanban_dashboard')
    kanban_dashboard = fields.Text(compute='_compute_kanban_dashboard')

    def _compute_kanban_dashboard(self):
        for record in self:
            domain = []
            if record.code == 'sale_invoice':
                domain = [('contract_type', '=', 'sale'), ('generation_type', '=', 'invoice')]
            elif record.code == 'purchase_invoice':
                domain = [('contract_type', '=', 'purchase'), ('generation_type', '=', 'invoice')]
            elif record.code == 'sale_order':
                domain = [('contract_type', '=', 'sale'), ('generation_type', '=', 'sale')]
            
            contracts = self.env['contract.contract'].search(domain)
            has_contracts = len(contracts) > 0
            
            draft = contracts.filtered(lambda c: c.state == 'draft')
            in_progress = contracts.filtered(lambda c: c.state == 'in_progress')
            done = contracts.filtered(lambda c: c.state == 'done')
            
            total_amount = 0.0
            company_currency = self.env.company.currency_id
            today = fields.Date.today()
            
            for contract in in_progress:
                contract_amount = sum(contract.contract_line_ids.mapped('price_subtotal'))
                if contract.currency_id and company_currency and contract.currency_id != company_currency:
                    contract_amount = contract.currency_id._convert(
                        contract_amount, 
                        company_currency, 
                        self.env.company, 
                        today
                    )
                total_amount += contract_amount

            # Formatear el total (simplificado)
            currency = self.env.company.currency_id
            formatted_amount = f"{currency.symbol} {total_amount:,.2f}" if currency else str(total_amount)

            dashboard_data = {
                'count_draft': len(draft),
                'count_in_progress': len(in_progress),
                'count_done': len(done),
                'total_amount': formatted_amount,
            }
            
            record.has_contracts = has_contracts
            record.kanban_dashboard = json.dumps(dashboard_data)

    def action_open_draft(self):
        return self._get_action('draft')

    def action_open_in_progress(self):
        return self._get_action('in_progress')
        
    def action_open_done(self):
        return self._get_action('done')
        
    def action_open_all(self):
        return self._get_action(None)

    def _get_action(self, state=None):
        self.ensure_one()
        
        # Obtener la acción base nativa para preservar todas las vistas (kanban, gantt, etc)
        if self.code in ['sale_invoice', 'sale_order']:
            action = self.env['ir.actions.act_window']._for_xml_id('contract.action_customer_contract')
        else:
            action = self.env['ir.actions.act_window']._for_xml_id('contract.action_supplier_contract')
            
        domain = []
        context = {}
        if self.code == 'sale_invoice':
            domain = [('contract_type', '=', 'sale'), ('generation_type', '=', 'invoice')]
            context = {'default_contract_type': 'sale', 'default_generation_type': 'invoice'}
        elif self.code == 'purchase_invoice':
            domain = [('contract_type', '=', 'purchase'), ('generation_type', '=', 'invoice')]
            context = {'default_contract_type': 'purchase', 'default_generation_type': 'invoice'}
        elif self.code == 'sale_order':
            domain = [('contract_type', '=', 'sale'), ('generation_type', '=', 'sale')]
            context = {'default_contract_type': 'sale', 'default_generation_type': 'sale'}
            
        if state:
            domain.append(('state', '=', state))
            
        action['domain'] = domain
        action['context'] = context
        action['name'] = self.name
        
        return action
