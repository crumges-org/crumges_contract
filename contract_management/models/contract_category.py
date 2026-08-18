from odoo import models, fields, api

class ContractCategory(models.Model):
    _name = 'contract.category'
    _description = 'Contract Category'

    name = fields.Char(string='Categoría', required=True, translate=True)
    base_type = fields.Selection([
        ('sale_order', 'Ventas (Pedidos)'),
        ('sale_invoice', 'Facturas de Venta Recurrentes'),
        ('purchase_invoice', 'Facturas de Compra Recurrentes')
    ], string='Tipo Base', required=True)
    contract_template_id = fields.Many2one('contract.template', string='Plantilla por Defecto')
    color = fields.Integer(string='Color Index')
    active = fields.Boolean(default=True)
    
    count_draft = fields.Integer(compute='_compute_contract_counts')
    count_in_progress = fields.Integer(compute='_compute_contract_counts')
    count_done = fields.Integer(compute='_compute_contract_counts')
    count_cancelled = fields.Integer(compute='_compute_contract_counts')
    count_paused = fields.Integer(compute='_compute_contract_counts')
    
    def _compute_contract_counts(self):
        for category in self:
            domain = [('category_id', '=', category.id)]
            contracts = self.env['contract.contract'].search(domain)
            
            category.count_draft = len(contracts.filtered(lambda c: c.state == 'draft'))
            category.count_in_progress = len(contracts.filtered(lambda c: c.state == 'in_progress'))
            category.count_done = len(contracts.filtered(lambda c: c.state == 'done'))
            category.count_cancelled = len(contracts.filtered(lambda c: c.state == 'cancelled'))
            category.count_paused = len(contracts.filtered(lambda c: c.state == 'paused'))

    def _get_action(self, state=None):
        self.ensure_one()
        
        if self.base_type == 'sale_invoice':
            action = self.env['ir.actions.act_window']._for_xml_id('contract_management.action_customer_invoice_contract')
            context = {'default_contract_type': 'sale', 'default_generation_type': 'invoice', 'default_sale_generation_type': 'invoice', 'default_category_id': self.id}
        elif self.base_type == 'sale_order':
            action = self.env['ir.actions.act_window']._for_xml_id('contract_management.action_customer_sale_contract')
            context = {'default_contract_type': 'sale', 'default_generation_type': 'sale', 'default_sale_generation_type': 'sale', 'default_category_id': self.id}
        else:
            action = self.env['ir.actions.act_window']._for_xml_id('contract_management.action_supplier_invoice_contract')
            context = {'default_contract_type': 'purchase', 'default_generation_type': 'invoice', 'default_purchase_generation_type': 'invoice', 'default_category_id': self.id}
            
        domain = action.get('domain', [])
        if isinstance(domain, str):
            import ast
            try:
                domain = ast.literal_eval(domain)
            except:
                domain = []
                
        domain.append(('category_id', '=', self.id))
            
        if state:
            domain.append(('state', '=', state))
            
        if self.contract_template_id:
            context['default_contract_template_id'] = self.contract_template_id.id
            
        action['domain'] = domain
        action['context'] = context
        action['name'] = self.name
        
        return action

    def action_open_draft(self):
        return self._get_action('draft')

    def action_open_in_progress(self):
        return self._get_action('in_progress')
        
    def action_open_done(self):
        return self._get_action('done')
        
    def action_open_cancelled(self):
        return self._get_action('cancelled')
        
    def action_open_paused(self):
        return self._get_action('paused')
        
    def action_open_all(self):
        return self._get_action(None)

