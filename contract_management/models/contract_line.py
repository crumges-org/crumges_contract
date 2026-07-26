from odoo import models, api, fields

class ContractLine(models.Model):
    _inherit = 'contract.line'

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
