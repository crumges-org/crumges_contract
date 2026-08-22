import logging
logger = logging.getLogger(__name__)
from odoo import api, fields, models


class ContractLine(models.Model):
    _inherit = "contract.line"

    @api.depends(
        "contract_id.recurring_next_date",
        "contract_id.line_recurrence",
        "last_date_invoiced",
        "date_start",
        "recurring_rule_type",
        "recurring_interval",
    )
    def _compute_recurring_next_date(self):
        for line in self:
            if (
                line.contract_id
                and not line.contract_id.line_recurrence
                and line.contract_id.recurring_next_date
                and not line.last_date_invoiced
            ):
                # Si la recurrencia es del contrato y la línea es nueva (no se ha facturado), hereda la fecha.
                line.recurring_next_date = line.contract_id.recurring_next_date
            else:
                # Calculamos manualmente la proxima fecha usando el metodo del mixin.
                # Evitamos usar super() porque contract.template.line (de la OCA) sobrescribe este
                # metodo y revierte la fecha a la del contrato ANTES de que el contrato
                # tenga oportunidad de actualizarse, causando un bug masivo de fechas congeladas.
                line.recurring_next_date = self.env[
                    "contract.recurring.mixin"
                ].get_next_invoice_date(
                    line.next_period_date_start,
                    line.recurring_invoicing_type,
                    line.recurring_invoicing_offset,
                    line.recurring_rule_type,
                    line.recurring_interval,
                    max_date_end=line.date_end,
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("contract_id"):
                contract = self.env["contract.contract"].browse(vals["contract_id"])
                if not contract.line_recurrence:
                    vals["recurring_rule_type"] = contract.recurring_rule_type
                    vals["recurring_interval"] = contract.recurring_interval
                    vals["recurring_invoicing_type"] = contract.recurring_invoicing_type
        records = super().create(vals_list)
        for record in records:
            self.env["contract.modification.rule"].evaluate_rules(record, "create", {})
        return records

    recurring_next_date = fields.Date(
        string="Próxima Generación",
        compute="_compute_recurring_next_date",
        store=True,
        readonly=False,
        copy=True,
    )
    last_date_invoiced = fields.Date(string="Última Generación")

    def write(self, vals):
        old_vals = {
            rec.id: {k: rec[k] for k in vals if k in rec._fields} for rec in self
        }
        res = super().write(vals)
        for rec in self:
            self.env["contract.modification.rule"].evaluate_rules(
                rec, "write", vals, old_vals.get(rec.id, {})
            )

            # Si el contrato no tiene line_recurrence, forzamos la sincronizacion para evitar asincronías
            if rec.contract_id and not rec.contract_id.line_recurrence:
                updates = {}
                if rec.recurring_rule_type != rec.contract_id.recurring_rule_type:
                    updates["recurring_rule_type"] = rec.contract_id.recurring_rule_type
                if rec.recurring_interval != rec.contract_id.recurring_interval:
                    updates["recurring_interval"] = rec.contract_id.recurring_interval
                if (
                    rec.recurring_invoicing_type
                    != rec.contract_id.recurring_invoicing_type
                ):
                    updates["recurring_invoicing_type"] = (
                        rec.contract_id.recurring_invoicing_type
                    )
                if updates:
                    super(ContractLine, rec).write(updates)

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

    replaced_by_line_id = fields.Many2one(
        "contract.line",
        string="Reemplazado Por",
        readonly=True,
        copy=False,
        help="Línea que reemplazó a esta línea actual.",
    )
    replaces_line_id = fields.Many2one(
        "contract.line",
        string="Reemplaza A",
        readonly=True,
        copy=False,
        help="Línea anterior que fue reemplazada por esta nueva línea.",
    )

    @api.onchange("product_id")
    def _onchange_product_id_legend(self):
        # Cuando se agrega o cambia un producto en la línea, si el contrato tiene la leyenda concatenada activa,
        # agregamos el sufijo automáticamente.
        if (
            self.contract_id
            and self.contract_id.add_period_legend
            and self.contract_id.period_legend_location == "product"
        ):
            if self.name and not self.display_type:
                legend_str = self.contract_id._get_legend_string(
                    self.contract_id.period_legend_type
                )
                if legend_str and legend_str not in self.name:
                    self.name = f"{self.name} - {legend_str}"

    product_template_id = fields.Many2one(
        "product.template",
        string="Plantilla de Producto",
        domain=[("sale_ok", "=", True)],
    )

    is_configurable_product = fields.Boolean(
        "Es Configurable", compute="_compute_is_configurable_product"
    )

    @api.depends("product_template_id")
    def _compute_is_configurable_product(self):
        for line in self:
            logger.info(
                "COMPUTE CALLED FOR LINE",
                line.id,
                "LAST DATE INVOICED:",
                line.last_date_invoiced,
            )
            line.is_configurable_product = (
                line.product_template_id
                and line.product_template_id.has_configurable_attributes
            )

    @api.onchange("product_template_id")
    def _onchange_product_template_id(self):
        if self.product_template_id:
            # If the product is not configurable (no attributes or just 1 variant), set product_id directly
            if not self.is_configurable_product:
                variant = self.product_template_id.product_variant_id
                if variant:
                    self.product_id = variant
                    # explicitly call the base onchange
                    if hasattr(self, "_onchange_product_id"):
                        self._onchange_product_id()
            else:
                self.product_id = False
        else:
            self.product_id = False

    variant_description = fields.Char(compute="_compute_variant_description")

    @api.depends("product_id", "product_template_id")
    def _compute_variant_description(self):
        for line in self:
            logger.info(
                "COMPUTE CALLED FOR LINE",
                line.id,
                "LAST DATE INVOICED:",
                line.last_date_invoiced,
            )
            if line.product_id and line.product_id.product_template_attribute_value_ids:
                desc = []
                for ptav in line.product_id.product_template_attribute_value_ids:
                    desc.append(f"{ptav.attribute_id.name}: {ptav.name}")
                line.variant_description = (
                    f"{line.product_template_id.name} ({', '.join(desc)})"
                )
            elif line.product_template_id:
                line.variant_description = line.product_template_id.name
            else:
                line.variant_description = ""

    @api.depends("contract_id.generation_type")
    def _compute_automatic_price(self):
        for line in self:
            logger.info(
                "COMPUTE CALLED FOR LINE",
                line.id,
                "LAST DATE INVOICED:",
                line.last_date_invoiced,
            )
            if (
                hasattr(line.contract_id, "generation_type")
                and line.contract_id.generation_type
            ):
                line.automatic_price = line.contract_id.generation_type == "sale"
            else:
                line.automatic_price = line.contract_id.contract_type == "sale"

    @api.constrains("recurring_next_date", "date_end", "last_date_invoiced")
    def _check_recurring_next_date_recurring_invoices(self):
        draft_lines = self.filtered(lambda l: l.contract_id.state == "draft")
        active_lines = self - draft_lines
        if active_lines and hasattr(
            super(ContractLine, active_lines),
            "_check_recurring_next_date_recurring_invoices",
        ):
            return super(
                ContractLine, active_lines
            )._check_recurring_next_date_recurring_invoices()

    @api.constrains("date_start", "recurring_next_date")
    def _check_recurring_next_date_start_date(self):
        # 1. Skip validation for draft contracts
        # 2. Skip validation for contracts without line_recurrence
        # When line_recurrence is False, the line's recurring_next_date is synced from the contract.
        # If a line is added mid-period, its date_start can be greater than the contract's recurring_next_date,
        # which causes a false positive ValidationError in OCA contract.
        valid_lines = self.filtered(
            lambda l: l.contract_id.state != "draft" and l.contract_id.line_recurrence
        )
        if valid_lines and hasattr(
            super(ContractLine, valid_lines), "_check_recurring_next_date_start_date"
        ):
            return super(
                ContractLine, valid_lines
            )._check_recurring_next_date_start_date()


class ContractTemplateLine(models.Model):
    _name = "contract.template.line"
    _inherit = ["contract.template.line", "analytic.mixin"]

    product_template_id = fields.Many2one(
        "product.template",
        string="Plantilla de Producto",
        domain=[("sale_ok", "=", True)],
    )

    is_configurable_product = fields.Boolean(
        "Es Configurable", compute="_compute_is_configurable_product"
    )

    @api.depends("product_template_id")
    def _compute_is_configurable_product(self):
        for line in self:
            logger.info(
                "COMPUTE CALLED FOR LINE",
                line.id,
                "LAST DATE INVOICED:",
                line.last_date_invoiced,
            )
            line.is_configurable_product = (
                line.product_template_id
                and line.product_template_id.has_configurable_attributes
            )

    @api.onchange("product_template_id")
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

    variant_description = fields.Char(compute="_compute_variant_description")

    @api.depends("product_id", "product_template_id")
    def _compute_variant_description(self):
        for line in self:
            logger.info(
                "COMPUTE CALLED FOR LINE",
                line.id,
                "LAST DATE INVOICED:",
                line.last_date_invoiced,
            )
            if line.product_id and line.product_id.product_template_attribute_value_ids:
                desc = []
                for ptav in line.product_id.product_template_attribute_value_ids:
                    desc.append(f"{ptav.attribute_id.name}: {ptav.name}")
                line.variant_description = (
                    f"{line.product_template_id.name} ({', '.join(desc)})"
                )
            elif line.product_template_id:
                line.variant_description = line.product_template_id.name
            else:
                line.variant_description = ""

    @api.depends("contract_id.generation_type")
    def _compute_automatic_price(self):
        for line in self:
            logger.info(
                "COMPUTE CALLED FOR LINE",
                line.id,
                "LAST DATE INVOICED:",
                line.last_date_invoiced,
            )
            if (
                hasattr(line.contract_id, "generation_type")
                and line.contract_id.generation_type
            ):
                line.automatic_price = line.contract_id.generation_type == "sale"
            else:
                line.automatic_price = line.contract_id.contract_type == "sale"
