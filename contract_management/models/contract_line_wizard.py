from odoo import models


class ContractLine(models.Model):
    _inherit = "contract.line"

    def action_open_variant_wizard(self):
        self.ensure_one()
        return {
            "name": "Configurar Producto",
            "type": "ir.actions.act_window",
            "res_model": "generic.variant.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_model": self._name,
                "active_id": self.id,
                "default_product_template_id": self.product_id.product_tmpl_id.id
                if self.product_id
                else False,
            },
        }


class ContractTemplateLine(models.Model):
    _inherit = "contract.template.line"

    def action_open_variant_wizard(self):
        self.ensure_one()
        return {
            "name": "Configurar Producto",
            "type": "ir.actions.act_window",
            "res_model": "generic.variant.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_model": self._name,
                "active_id": self.id,
                "default_product_template_id": self.product_id.product_tmpl_id.id
                if self.product_id
                else False,
            },
        }
