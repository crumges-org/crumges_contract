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

    # Bloque: Motores de Generación
    group_contract_sale_invoice = fields.Boolean(
        string="Generar Facturas de Venta",
        implied_group="contract_management.group_contract_sale_invoice",
        help="Habilita la generación de facturas recurrentes a clientes.",
    )
    group_contract_sale_order = fields.Boolean(
        string="Generar Pedidos de Venta",
        implied_group="contract_management.group_contract_sale_order",
        help="Habilita la generación de órdenes de venta (Presupuestos/Pedidos).",
    )
    group_contract_purchase_invoice = fields.Boolean(
        string="Generar Facturas de Compra",
        implied_group="contract_management.group_contract_purchase_invoice",
        help="Habilita la generación de facturas recurrentes de proveedores.",
    )
    module_contract_sale_generation = fields.Boolean(
        string="Módulo OCA: contract_sale_generation"
    )



    # Bloque: Vistas Adicionales
    module_contract_management_timeline = fields.Boolean(
        string="Vista de Línea de Tiempo (Community)"
    )
    module_contract_management_gantt_ee = fields.Boolean(
        string="Vista Gantt (Enterprise)"
    )

    @api.onchange("group_contract_sale_order")
    def _onchange_group_contract_sale_order(self):
        for rec in self:
            rec.module_contract_sale_generation = rec.group_contract_sale_order

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
