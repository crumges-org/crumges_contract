from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    group_contract_template = fields.Boolean(
        string="Usar Plantillas de Contrato",
        implied_group="contract_management.group_contract_template",
        help="Habilita el menú y funcionalidad de Plantillas del Contrato.",
    )
    group_contract_tag = fields.Boolean(
        string="Usar Etiquetas de Contrato",
        implied_group="contract_management.group_contract_tag",
        help="Habilita el menú y funcionalidad de Etiquetas de Contrato.",
    )
    group_contract_line_recurrence = fields.Boolean(
        string="Recurrencia a nivel de línea",
        implied_group="contract_management.group_contract_line_recurrence",
        help="Permite definir reglas de facturación recurrentes diferentes para cada línea del contrato.",
    )
    group_contract_modification_rule = fields.Boolean(
        string="Gestión de cambios automáticos",
        implied_group="contract_management.group_contract_modification_rule",
        help="Habilita el menú de Reglas de Modificación para automatizar cambios en los contratos.",
    )
    module_contract_variable_qty_prorated = fields.Boolean(
        string="Prorrateo de Cantidades Variables",
        help="Permite aplicar reglas de prorrateo a las fórmulas y consumos variables a mitad de mes.",
    )

    # Bloque: Vistas Adicionales
    enable_gantt_view = fields.Boolean(
        string="Activar Vista Gantt / Timeline",
        config_parameter="contract_management.enable_gantt_view",
    )
    gantt_view_type = fields.Selection(
        [
            ("community", "Gantt Community"),
            ("enterprise", "Gantt Enterprise"),
        ],
        string="Tipo de Vista",
        config_parameter="contract_management.gantt_view_type",
    )
    module_contract_management_timeline = fields.Boolean()
    module_contract_management_gantt_ee = fields.Boolean()

    @api.onchange("enable_gantt_view", "gantt_view_type")
    def _onchange_gantt_view_selection(self):
        for rec in self:
            if rec.enable_gantt_view:
                if rec.gantt_view_type == "community":
                    rec.module_contract_management_timeline = True
                    rec.module_contract_management_gantt_ee = False
                elif rec.gantt_view_type == "enterprise":
                    rec.module_contract_management_timeline = False
                    rec.module_contract_management_gantt_ee = True
                else:
                    rec.module_contract_management_timeline = False
                    rec.module_contract_management_gantt_ee = False
            else:
                rec.module_contract_management_timeline = False
                rec.module_contract_management_gantt_ee = False
                rec.gantt_view_type = False

    @api.onchange("module_contract_management_timeline")
    def _onchange_timeline(self):
        for rec in self:
            if rec.module_contract_management_timeline:
                rec.module_contract_management_gantt_ee = False

    @api.onchange("module_contract_management_gantt_ee")
    def _onchange_gantt(self):
        for rec in self:
            if rec.module_contract_management_gantt_ee:
                rec.module_contract_management_timeline = False
