from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    contract_ids = fields.Many2many(
        "contract.contract", compute="_compute_contract_ids", string="Contracts"
    )
    contract_count = fields.Integer(
        compute="_compute_contract_ids", string="Contract Count"
    )

    @api.depends("invoice_line_ids.contract_line_id.contract_id")
    def _compute_contract_ids(self):
        for move in self:
            contracts = move.invoice_line_ids.mapped("contract_line_id.contract_id")
            move.contract_ids = contracts
            move.contract_count = len(contracts)

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
