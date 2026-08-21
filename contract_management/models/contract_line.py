from odoo import models, api, fields

class ContractLine(models.Model):
    _inherit = 'contract.line'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            self.env['contract.modification.rule'].evaluate_rules(record, 'create', {})
        return records

    def write(self, vals):
        old_vals = {rec.id: {k: rec[k] for k in vals if k in rec._fields} for rec in self}
        res = super().write(vals)
        for rec in self:
            self.env['contract.modification.rule'].evaluate_rules(rec, 'write', vals, old_vals.get(rec.id, {}))
        return res

    recurring_invoicing_type = fields.Selection(
        [
            ("pre-paid", "Al inicio del periodo"),
            ("post-paid", "Al finalizar el periodo"),
        ],
        string="Momento de Generación",
        default="pre-paid",
        required=True,
    )
    
    recurring_next_date = fields.Date(string="Próxima Generación")
    last_date_invoiced = fields.Date(string="Última Generación")

    @api.onchange('product_id')
    def _onchange_product_id_legend(self):
        # Cuando se agrega o cambia un producto en la línea, si el contrato tiene la leyenda concatenada activa,
        # agregamos el sufijo automáticamente.
        if self.contract_id and self.contract_id.add_period_legend and self.contract_id.period_legend_location == 'product':
            if self.name and not self.display_type:
                legend_str = self.contract_id._get_legend_string(self.contract_id.period_legend_type)
                if legend_str and legend_str not in self.name:
                    self.name = f"{self.name} - {legend_str}"

    product_template_id = fields.Many2one(
        'product.template',
        string='Plantilla de Producto',
        domain=[('sale_ok', '=', True)]
    )

    is_configurable_product = fields.Boolean(
        'Es Configurable',
        compute='_compute_is_configurable_product'
    )

    @api.depends('product_template_id')
    def _compute_is_configurable_product(self):
        for line in self:
            line.is_configurable_product = line.product_template_id and line.product_template_id.has_configurable_attributes

    @api.onchange('product_template_id')
    def _onchange_product_template_id(self):
        if self.product_template_id:
            # If the product is not configurable (no attributes or just 1 variant), set product_id directly
            if not self.is_configurable_product:
                variant = self.product_template_id.product_variant_id
                if variant:
                    self.product_id = variant
                    # explicitly call the base onchange
                    if hasattr(self, '_onchange_product_id'):
                        self._onchange_product_id()
            else:
                self.product_id = False
        else:
            self.product_id = False

    variant_description = fields.Char(compute='_compute_variant_description')

    @api.depends('product_id', 'product_template_id')
    def _compute_variant_description(self):
        for line in self:
            if line.product_id and line.product_id.product_template_attribute_value_ids:
                desc = []
                for ptav in line.product_id.product_template_attribute_value_ids:
                    desc.append(f"{ptav.attribute_id.name}: {ptav.name}")
                line.variant_description = f"{line.product_template_id.name} ({', '.join(desc)})"
            elif line.product_template_id:
                line.variant_description = line.product_template_id.name
            else:
                line.variant_description = ""

    @api.depends("contract_id.generation_type")
    def _compute_automatic_price(self):
        for line in self:
            if hasattr(line.contract_id, 'generation_type') and line.contract_id.generation_type:
                line.automatic_price = line.contract_id.generation_type == "sale"
            else:
                line.automatic_price = line.contract_id.contract_type == "sale"

    @api.constrains('recurring_next_date', 'date_end', 'last_date_invoiced')
    def _check_recurring_next_date_recurring_invoices(self):
        draft_lines = self.filtered(lambda l: l.contract_id.state == 'draft')
        active_lines = self - draft_lines
        if active_lines and hasattr(super(ContractLine, active_lines), '_check_recurring_next_date_recurring_invoices'):
            super(ContractLine, active_lines)._check_recurring_next_date_recurring_invoices()

    @api.constrains('date_start', 'recurring_next_date')
    def _check_recurring_next_date_start_date(self):
        draft_lines = self.filtered(lambda l: l.contract_id.state == 'draft')
        active_lines = self - draft_lines
        if active_lines and hasattr(super(ContractLine, active_lines), '_check_recurring_next_date_start_date'):
            super(ContractLine, active_lines)._check_recurring_next_date_start_date()

class ContractTemplateLine(models.Model):
    _name = 'contract.template.line'
    _inherit = ['contract.template.line', 'analytic.mixin']

    product_template_id = fields.Many2one(
        'product.template',
        string='Plantilla de Producto',
        domain=[('sale_ok', '=', True)]
    )

    is_configurable_product = fields.Boolean(
        'Es Configurable',
        compute='_compute_is_configurable_product'
    )

    @api.depends('product_template_id')
    def _compute_is_configurable_product(self):
        for line in self:
            line.is_configurable_product = line.product_template_id and line.product_template_id.has_configurable_attributes

    @api.onchange('product_template_id')
    def _onchange_product_template_id(self):
        if self.product_template_id:
            if not self.is_configurable_product:
                variant = self.product_template_id.product_variant_id
                if variant:
                    self.product_id = variant
            else:
                self.product_id = False
        else:
            self.product_id = False

    variant_description = fields.Char(compute='_compute_variant_description')

    @api.depends('product_id', 'product_template_id')
    def _compute_variant_description(self):
        for line in self:
            if line.product_id and line.product_id.product_template_attribute_value_ids:
                desc = []
                for ptav in line.product_id.product_template_attribute_value_ids:
                    desc.append(f"{ptav.attribute_id.name}: {ptav.name}")
                line.variant_description = f"{line.product_template_id.name} ({', '.join(desc)})"
            elif line.product_template_id:
                line.variant_description = line.product_template_id.name
            else:
                line.variant_description = ""

    @api.depends("contract_id.generation_type")
    def _compute_automatic_price(self):
        for line in self:
            if hasattr(line.contract_id, 'generation_type') and line.contract_id.generation_type:
                line.automatic_price = line.contract_id.generation_type == "sale"
            else:
                line.automatic_price = line.contract_id.contract_type == "sale"
