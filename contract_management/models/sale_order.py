from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    contract_ids = fields.Many2many(
        "contract.contract", compute="_compute_contract_ids"
    )
    contract_count = fields.Integer(compute="_compute_contract_ids")

    @api.depends("order_line.contract_line_id.contract_id")
    def _compute_contract_ids(self):
        for order in self:
            contracts = order.order_line.mapped("contract_line_id.contract_id")
            order.contract_ids = contracts
            order.contract_count = len(contracts)

    def action_view_contracts(self):
        self.ensure_one()
        contracts = self.contract_ids

        action = {
            "name": "Contratos",
            "type": "ir.actions.act_window",
            "res_model": "contract.contract",
            "view_mode": "kanban,list,form",
        }
        if len(contracts) == 1:
            action["views"] = [
                (self.env.ref("contract.contract_contract_form_view").id, "form")
            ]
            action["res_id"] = (
                contracts.id.id if hasattr(contracts.id, "id") else contracts.id
            )
        else:
            action["domain"] = [("id", "in", contracts.ids)]

        return action
