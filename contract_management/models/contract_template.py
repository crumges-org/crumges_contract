from odoo import models, fields, api

class ContractTemplate(models.Model):
    _name = 'contract.template'
    _inherit = ['contract.template', 'analytic.mixin']

    sale_autoconfirm = fields.Boolean(
        string="Confirmar Pedidos Automáticamente",
        help="Si se marca, los pedidos de venta generados desde esta plantilla se confirmarán automáticamente.",
        default=True
    )
    auto_post_invoice = fields.Boolean(
        string="Confirmar Facturas Automáticamente",
        help="Si se marca, las facturas generadas desde esta plantilla se publicarán automáticamente.",
        default=True
    )
    color = fields.Integer(string='Color Index')
    
    count_draft = fields.Integer(compute='_compute_contract_counts')
    count_in_progress = fields.Integer(compute='_compute_contract_counts')
    count_done = fields.Integer(compute='_compute_contract_counts')
    count_cancelled = fields.Integer(compute='_compute_contract_counts')
    count_paused = fields.Integer(compute='_compute_contract_counts')
    
    # Nuevos campos solicitados
    payment_term_id = fields.Many2one(
        'account.payment.term', 
        string='Términos de Pago'
    )
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', 
        string='Posición Fiscal'
    )
    tag_ids = fields.Many2many(
        'contract.tag', 
        string='Etiquetas'
    )
    add_period_legend = fields.Boolean(
        string="Agregar leyenda de periodo",
        default=False
    )
    period_legend_text = fields.Char(
        string="Texto Previo",
        help="Ej: 'Periodo facturado:'. Se omitirá si se deja vacío."
    )
    period_legend_type = fields.Selection(
        [('period', 'Periodo'), ('month', 'Mes')],
        string="Tipo de Leyenda",
        default='period'
    )
    period_legend_location = fields.Selection(
        [('product', 'Concatenada al producto'), ('note', 'En una nota')],
        string="Lugar de la Leyenda",
        default='product'
    )
    description = fields.Html(
        string="Descripción / Propósito"
    )
    icon = fields.Char(
        string="Icono"
    )
    active = fields.Boolean(
        string="Activo", 
        default=True,
        help="Si desmarcas esta casilla, la plantilla se ocultará sin ser eliminada."
    )

    terms_and_conditions = fields.Html(
        string="Términos y Condiciones"
    )
    note = fields.Html(
        string="Notas Internas"
    )

    @api.onchange('contract_type')
    def _onchange_contract_type(self):
        for template in self:
            if template.contract_type == 'purchase':
                # Attempt to set generation_type to invoice if the field exists
                if hasattr(template, 'generation_type'):
                    template.generation_type = 'invoice'

    def _compute_contract_counts(self):
        for template in self:
            domain = [('contract_template_id', '=', template.id)]
            contracts = self.env['contract.contract'].search(domain)
            
            template.count_draft = len(contracts.filtered(lambda c: c.state == 'draft'))
            template.count_in_progress = len(contracts.filtered(lambda c: c.state == 'in_progress'))
            template.count_done = len(contracts.filtered(lambda c: c.state == 'done'))
            template.count_cancelled = len(contracts.filtered(lambda c: c.state == 'cancelled'))
            template.count_paused = len(contracts.filtered(lambda c: c.state == 'paused'))

    def _get_action(self, state=None):
        self.ensure_one()
        
        # Determine base logic from contract_type and generation_type
        if self.contract_type == 'purchase':
            action = self.env['ir.actions.act_window']._for_xml_id('contract_management.action_supplier_invoice_contract')
            context = {'default_contract_type': 'purchase', 'default_generation_type': 'invoice', 'default_purchase_generation_type': 'invoice', 'default_contract_template_id': self.id, 'default_auto_post_invoice': self.auto_post_invoice}
        elif self.contract_type == 'sale' and getattr(self, 'generation_type', 'invoice') == 'sale':
            action = self.env['ir.actions.act_window']._for_xml_id('contract_management.action_customer_sale_contract')
            context = {'default_contract_type': 'sale', 'default_generation_type': 'sale', 'default_sale_generation_type': 'sale', 'default_contract_template_id': self.id, 'default_sale_autoconfirm': self.sale_autoconfirm}
        else:
            action = self.env['ir.actions.act_window']._for_xml_id('contract_management.action_customer_invoice_contract')
            context = {'default_contract_type': 'sale', 'default_generation_type': 'invoice', 'default_sale_generation_type': 'invoice', 'default_contract_template_id': self.id, 'default_auto_post_invoice': self.auto_post_invoice}
            
        domain = action.get('domain', [])
        if isinstance(domain, str):
            import ast
            try:
                domain = ast.literal_eval(domain)
            except:
                domain = []
                
        domain.append(('contract_template_id', '=', self.id))
            
        if state:
            domain.append(('state', '=', state))
            
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

    @api.onchange('analytic_distribution')
    def _onchange_analytic_distribution_header(self):
        """Propaga la distribución analítica de la cabecera a todas las líneas."""
        if self.analytic_distribution:
            for line in self.contract_line_ids:
                line.analytic_distribution = self.analytic_distribution
