from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Contract(models.Model):
    _name = "contract.contract"
    _inherit = ["contract.contract", "analytic.mixin"]

    # Nomenclatura Genérica: En lugar de usar términos de "factura" en el código custom,
    # preferimos términos genéricos.
    recurring_invoicing_type = fields.Selection(
        [
            ("pre-paid", "Al inicio del periodo"),
            ("post-paid", "Al finalizar el periodo"),
        ],
        string="Momento de Generación",
        required=True,
    )

    import logging

    _logger = logging.getLogger(__name__)

    manual_recurring_next_date = fields.Date(
        string="Fecha manual de proxima generacion", copy=False
    )

    recurring_next_date = fields.Date(
        string="Próxima Generación", inverse="_inverse_recurring_next_date"
    )

    def _inverse_recurring_next_date(self):
        for contract in self:
            self._logger.info(
                "INVERSE FIRED FOR CONTRACT %s. DATE: %s",
                contract.id,
                contract.recurring_next_date,
            )
            # When user manually changes the contract's recurring next date,
            # push it to all uninvoiced lines if recurrence is at contract level.
            # This prevents OCA's compute from reverting the contract date back to the old line date.
            if not contract.line_recurrence and contract.recurring_next_date:
                contract.manual_recurring_next_date = contract.recurring_next_date
                lines_to_update = contract.contract_line_ids.filtered(
                    lambda l: not l.last_date_invoiced and not l.is_canceled
                )
                self._logger.info("LINES TO UPDATE: %s", lines_to_update.ids)
                for line in lines_to_update:
                    line.recurring_next_date = contract.recurring_next_date
                    self._logger.info(
                        "SET LINE %s DATE TO %s", line.id, line.recurring_next_date
                    )

    last_date_invoiced = fields.Date(string="Última Generación")

    auto_post_invoice = fields.Boolean(
        string="Validar Facturas Automáticamente",
        default=True,
        help="Si está marcado, las facturas generadas por este contrato se publicarán automáticamente.",
    )

    skip_zero_qty = fields.Boolean(
        default=True,
        help="Si está marcado, las líneas con cantidad cero se omitirán en la generación.",
    )

    sale_autoconfirm = fields.Boolean(
        string="Auto confirmar el pedido de venta",
        default=True,
        help="Si está marcado, los pedidos de venta generados por este contrato se confirmarán automáticamente.",
    )

    name = fields.Char(default=lambda self: _("New"), copy=False, readonly=True)

    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("in_progress", "En Curso"),
            ("done", "Finalizado"),
            ("cancelled", "Cancelado"),
            ("paused", "Pausado"),
        ],
        string="Estado",
        default="draft",
        tracking=True,
    )



    # Bloqueamos el cambio de plantilla si no es borrador y emulamos la protección de ventas
    safe_template_id = fields.Many2one(
        "contract.template",
        string="Plantilla de Contrato",
    )

    @api.onchange("safe_template_id")
    def _onchange_safe_template_id(self):
        if not self.safe_template_id:
            return

        if self.contract_line_ids:
            template = self.safe_template_id
            self.safe_template_id = False
            return {
                "warning": {
                    "title": _("Atención"),
                    "message": _(
                        'El contrato ya tiene líneas. Haga clic en "Aplicar Plantilla" si desea reemplazar o fusionar sus líneas actuales.'
                    ),
                }
            }
        else:
            self.contract_template_id = self.safe_template_id

            # Apply contract_type and generation_type logic from the template
            self.contract_type = self.safe_template_id.contract_type
            # Handle the generation_type (it could be defined in the template or default to invoice)
            self.generation_type = getattr(
                self.safe_template_id, "generation_type", "invoice"
            )

            # Propagate text fields
            if self.safe_template_id.description:
                self.description = self.safe_template_id.description
            if self.safe_template_id.icon:
                self.icon = self.safe_template_id.icon
            if self.safe_template_id.note:
                self.note = self.safe_template_id.note
            if self.safe_template_id.terms_and_conditions:
                self.terms_and_conditions = self.safe_template_id.terms_and_conditions

            self.safe_template_id = False

    def action_in_progress(self):
        for rec in self:
            rec.state = "in_progress"
            # Forzar las validaciones que fueron ignoradas en estado borrador
            if hasattr(
                rec.contract_line_ids, "_check_recurring_next_date_recurring_invoices"
            ):
                rec.contract_line_ids._check_recurring_next_date_recurring_invoices()
            if hasattr(rec.contract_line_ids, "_check_recurring_next_date_start_date"):
                rec.contract_line_ids._check_recurring_next_date_start_date()

    def action_draft(self):
        for rec in self:
            rec.state = "draft"

    def action_cancel(self):
        for rec in self:
            rec.state = "cancelled"

    def action_open_template_wizard(self):
        self.ensure_one()
        # TODO: Lógica para reutilizar el wizard de plantillas de ventas
        pass

    # Campo emulado para Proveedores (Oculta la opción Sale)
    purchase_generation_type = fields.Selection(
        [("invoice", "Invoice")],
        string="Generation Type",
        help="Defines what document is automatically generated by the cron.",
        required=True,
        compute="_compute_purchase_generation_type",
        inverse="_inverse_purchase_generation_type",
    )

    @api.depends("generation_type")
    def _compute_purchase_generation_type(self):
        for rec in self:
            rec.purchase_generation_type = "invoice"

    def _inverse_purchase_generation_type(self):
        for rec in self:
            if rec.contract_type == "purchase":
                rec.generation_type = "invoice"

    # Campo emulado para Clientes (Mantiene simetría y lo hace obligatorio)
    sale_generation_type = fields.Selection(
        [("sale", "Sale"), ("invoice", "Invoice")],
        string="Generation Type",
        help="Defines what document is automatically generated by the cron.",
        required=True,
        compute="_compute_sale_generation_type",
        inverse="_inverse_sale_generation_type",
    )

    description = fields.Html(string="Descripción / Propósito")
    icon = fields.Char(string="Icono")

    terms_and_conditions = fields.Html(string="Términos y Condiciones")
    note = fields.Html(string="Notas Internas")

    @api.depends("generation_type")
    def _compute_sale_generation_type(self):
        for rec in self:
            rec.sale_generation_type = rec.generation_type or "invoice"

    def _inverse_sale_generation_type(self):
        for rec in self:
            if rec.contract_type == "sale":
                rec.generation_type = rec.sale_generation_type



    # --- Leyenda Dinámica de Periodo ---
    add_period_legend = fields.Boolean(
        string="Agregar leyenda de periodo", default=False
    )
    period_legend_text = fields.Char(
        string="Texto Previo",
        help="Ej: 'Periodo facturado:'. Se omitirá si se deja vacío.",
    )
    period_legend_type = fields.Selection(
        [("period", "Periodo"), ("month", "Mes")],
        string="Tipo de Leyenda",
        default="period",
    )
    period_legend_location = fields.Selection(
        [("product", "Concatenada al producto"), ("note", "En una nota")],
        string="Lugar de la Leyenda",
        default="product",
    )

    def _get_legend_string(self, legend_type):
        base_marker = ""
        if legend_type == "period":
            base_marker = "#START# al #END#"
        elif legend_type == "month":
            base_marker = "#INVOICEMONTHNAME#"

        if not base_marker:
            return ""

        if self.period_legend_text:
            return f"{self.period_legend_text.strip()} {base_marker}"
        return base_marker

    @api.onchange(
        "add_period_legend",
        "period_legend_type",
        "period_legend_location",
        "period_legend_text",
    )
    def _onchange_period_legend(self):
        import re

        for rec in self:
            # Primero identificamos las notas de leyenda actuales
            legend_notes = rec.contract_line_ids.filtered(
                lambda l: l.display_type == "line_note"
                and l.name
                and ("#START#" in l.name or "#INVOICEMONTHNAME#" in l.name)
            )

            # Las eliminamos del RecordSet (esto limpia la UI inmediatamente)
            if legend_notes:
                rec.contract_line_ids -= legend_notes

            # Limpiamos los sufijos de los productos normales
            for line in rec.contract_line_ids.filtered(lambda l: not l.display_type):
                if line.name:
                    line.name = re.sub(
                        r" - .*?(#START# al #END#|#INVOICEMONTHNAME#)$", "", line.name
                    )

            # Si la leyenda está activa, aplicamos la nueva configuración
            if rec.add_period_legend:
                legend_str = rec._get_legend_string(rec.period_legend_type)
                if legend_str:
                    if rec.period_legend_location == "product":
                        # Concatenamos a los productos
                        for line in rec.contract_line_ids.filtered(
                            lambda l: not l.display_type
                        ):
                            if line.name:
                                line.name = f"{line.name} - {legend_str}"

                    elif rec.period_legend_location == "note":
                        # Agregamos una nueva nota pura usando .new()
                        max_seq = (
                            max(rec.contract_line_ids.mapped("sequence"))
                            if rec.contract_line_ids
                            else 10
                        )
                        rec.contract_line_ids += self.env["contract.line"].new(
                            {
                                "display_type": "line_note",
                                "name": legend_str,
                                "sequence": max_seq + 1,
                            }
                        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New") or not vals.get("name"):
                sequence_number = (
                    self.env["ir.sequence"].next_by_code("contract.contract") or ""
                )
                vals["name"] = sequence_number or _("New")

        records = super().create(vals_list)
        for record in records:
            self.env["contract.modification.rule"].evaluate_rules(record, "create", {})
        return records

    def write(self, vals):
        old_vals = {
            rec.id: {k: rec[k] for k in vals if k in rec._fields} for rec in self
        }
        res = super().write(vals)

        fields_to_sync = [
            "recurring_rule_type",
            "recurring_interval",
            "recurring_invoicing_type",
        ]
        if any(f in vals for f in fields_to_sync):
            for rec in self:
                if not rec.line_recurrence:
                    updates = {}
                    for f in fields_to_sync:
                        updates[f] = getattr(rec, f)
                    if updates:
                        rec.contract_line_ids.write(updates)

        for rec in self:
            self.env["contract.modification.rule"].evaluate_rules(
                rec, "write", vals, old_vals.get(rec.id, {})
            )
        # Asegurar que si la leyenda es tipo nota, siempre esté al final (mayor secuencia)
        for rec in self:
            if rec.add_period_legend and rec.period_legend_location == "note":
                legend_note = rec.contract_line_ids.filtered(
                    lambda l: l.display_type == "line_note"
                    and l.name
                    and l.name.startswith(rec.period_legend_text or "")
                )
                if legend_note:
                    max_seq = (
                        max(
                            rec.contract_line_ids.filtered(
                                lambda l: l.id != legend_note[0].id
                            ).mapped("sequence")
                        )
                        if len(rec.contract_line_ids) > 1
                        else 10
                    )
                    if legend_note[0].sequence <= max_seq:
                        legend_note[0].sequence = max_seq + 1
        return res

    def _prepare_invoice(self, date_invoice, journal=None):
        vals = super()._prepare_invoice(date_invoice, journal=journal)

        narration = Markup("")
        if self.terms_and_conditions:
            narration += self.terms_and_conditions

        if self.note:
            if narration:
                narration += Markup("<br/><br/>")
            narration += Markup("<b>Notas Internas:</b><br/>") + self.note

        if narration:
            vals["narration"] = narration

        return vals

    def _prepare_sale(self, date_ref):
        vals = super()._prepare_sale(date_ref)
        if self.terms_and_conditions:
            vals["note"] = self.terms_and_conditions
        # Usamos try/except por si el módulo que agrega internal_note a sales no está o cambia en el futuro
        try:
            if self.note:
                vals["internal_note"] = self.note
        except Exception:
            pass
        return vals
        return res

    # Extensión del Cron: Para evitar que Odoo genere documentos de contratos en borrador,
    # debemos filtrar en el dominio o sobreescribir el método de búsqueda de generación.
    # En la OCA, generalmente el método base es `_get_contracts_to_invoice()`.

    @api.model
    def _get_contracts_to_invoice_domain(self):
        """Sobrescribimos el dominio del cron para ignorar borradores"""
        # La forma exacta depende de la versión OCA, pero este es el dominio base
        domain = super()._get_contracts_to_invoice_domain()
        domain.append(("state", "=", "in_progress"))
        return domain

    def _recurring_create_invoice(self, date_ref=False):
        moves = super()._recurring_create_invoice(date_ref=date_ref)
        for move in moves.filtered("invoice_line_ids"):
            contracts = move.invoice_line_ids.mapped("contract_line_id.contract_id")
            if any(c.auto_post_invoice for c in contracts):
                move.action_post()

            # CLEAR THE MANUAL NEXT DATE SO THE CONTRACT CAN ADVANCE
            for c in contracts:
                c.manual_recurring_next_date = False

        return moves

    @api.model
    def get_global_dashboard_stats(self):
        from datetime import timedelta

        today = fields.Date.today()
        d7 = today + timedelta(days=7)
        d15 = today + timedelta(days=15)
        d30 = today + timedelta(days=30)
        d365 = today + timedelta(days=365)

        active_contracts = self.search([("state", "=", "in_progress")])

        # Conteo de estados globales
        state_groups = self.read_group([], ["state"], ["state"])
        state_counts = {g["state"]: g["state_count"] for g in state_groups}

        # Contratos con fecha de fin
        expiring_contracts = active_contracts.filtered(lambda c: c.date_end)

        exp_7 = len(expiring_contracts.filtered(lambda c: c.date_end <= d7))
        exp_15 = len(expiring_contracts.filtered(lambda c: d7 < c.date_end <= d15))
        exp_30 = len(expiring_contracts.filtered(lambda c: d15 < c.date_end <= d30))
        exp_365 = len(expiring_contracts.filtered(lambda c: d30 < c.date_end <= d365))

        total_revenue = 0
        company_currency = self.env.company.currency_id

        state_revenue = {"draft": 0, "in_progress": 0, "paused": 0}
        for contract in self.search(
            [("state", "in", ["draft", "in_progress", "paused"])]
        ):
            amount = sum(contract.contract_line_ids.mapped("price_subtotal"))
            if (
                contract.currency_id
                and company_currency
                and contract.currency_id != company_currency
            ):
                amount = contract.currency_id._convert(
                    amount, company_currency, self.env.company, today
                )
            state_revenue[contract.state] += amount
            if contract.state == "in_progress":
                total_revenue += amount

        total_expiring = exp_7 + exp_15 + exp_30 + exp_365

        def date_str(d):
            return d.strftime("%Y-%m-%d")

        # ==========================================
        # CALCULADORA DE TENDENCIAS (KPIs)
        # ==========================================
        trends = self.env["contract.dashboard.trend"].search([])
        trend_results = {
            "active_contracts": None,
            "total_revenue": None,
            "expiring_soon": None,
        }

        # Helper para calcular métricas en una fecha pasada
        def _get_metrics_at_date(target_date):
            domain = [
                ("state", "not in", ["draft", "cancelled"]),
                "|",
                ("date_start", "=", False),
                ("date_start", "<=", target_date),
            ]
            past_contracts = self.search(domain)
            # Descartar los que ya habían terminado en esa fecha
            past_active = past_contracts.filtered(
                lambda c: not c.date_end or c.date_end >= target_date
            )

            past_revenue = 0
            for c in past_active:
                amt = sum(c.contract_line_ids.mapped("price_subtotal"))
                if (
                    c.currency_id
                    and company_currency
                    and c.currency_id != company_currency
                ):
                    amt = c.currency_id._convert(
                        amt, company_currency, self.env.company, target_date
                    )
                past_revenue += amt

            past_expiring = len(
                past_active.filtered(
                    lambda c: c.date_end
                    and c.date_end <= target_date + timedelta(days=30)
                )
            )

            return len(past_active), past_revenue, past_expiring

        # Agrupar las reglas de tendencia requeridas
        required_periods = set(int(t.comparison_period) for t in trends)
        metrics_history = {}
        for p in required_periods:
            metrics_history[p] = _get_metrics_at_date(today - timedelta(days=p))

        current_metrics = {
            "active_contracts": len(active_contracts),
            "total_revenue": total_revenue,
            "expiring_soon": exp_30 + exp_15 + exp_7,  # Todos los menores a 30 días
        }

        for metric in trend_results.keys():
            metric_trends = trends.filtered(lambda t: t.metric_type == metric)
            for t in metric_trends:
                period = int(t.comparison_period)
                past_val = metrics_history[period][
                    0
                    if metric == "active_contracts"
                    else 1
                    if metric == "total_revenue"
                    else 2
                ]
                curr_val = current_metrics[metric]

                # Calcular crecimiento %
                growth = 0.0
                if past_val > 0:
                    growth = ((curr_val - past_val) / past_val) * 100
                elif curr_val > 0:
                    growth = 100.0  # Crecimiento infinito desde 0

                if t.evaluate_trend(growth):
                    trend_results[metric] = {
                        "legend": t.name,
                        "percentage": round(growth, 1),
                        "color": t.color,
                        "details": t.details,
                    }
                    break  # Tomar la primera regla que coincida (por sequence)

        # ==========================================

        return {
            "total_active": current_metrics["active_contracts"],
            "total_revenue": round(current_metrics["total_revenue"], 2),
            "total_expiring": total_expiring,
            "currency_symbol": company_currency.symbol or "$",
            "trends": trend_results,
            "state_revenue": {
                "draft": round(state_revenue.get("draft", 0), 2),
                "in_progress": round(state_revenue.get("in_progress", 0), 2),
                "paused": round(state_revenue.get("paused", 0), 2),
            },
            "states": {
                "draft": state_counts.get("draft", 0),
                "in_progress": state_counts.get("in_progress", 0),
                "paused": state_counts.get("paused", 0),
                "done": state_counts.get("done", 0),
                "cancelled": state_counts.get("cancelled", 0),
            },
            "expiring": {
                "d7": {
                    "count": exp_7,
                    "domain": [
                        ("state", "=", "in_progress"),
                        ("date_end", "!=", False),
                        ("date_end", "<=", date_str(d7)),
                    ],
                },
                "d15": {
                    "count": exp_15,
                    "domain": [
                        ("state", "=", "in_progress"),
                        ("date_end", "!=", False),
                        ("date_end", ">", date_str(d7)),
                        ("date_end", "<=", date_str(d15)),
                    ],
                },
                "d30": {
                    "count": exp_30,
                    "domain": [
                        ("state", "=", "in_progress"),
                        ("date_end", "!=", False),
                        ("date_end", ">", date_str(d15)),
                        ("date_end", "<=", date_str(d30)),
                    ],
                },
                "d365": {
                    "count": exp_365,
                    "domain": [
                        ("state", "=", "in_progress"),
                        ("date_end", "!=", False),
                        ("date_end", ">", date_str(d30)),
                        ("date_end", "<=", date_str(d365)),
                    ],
                },
            },
        }

    pending_modification_count = fields.Integer(
        string="Pending Modifications Count", compute="_compute_pending_modifications"
    )
    has_pending_modifications = fields.Boolean(
        compute="_compute_pending_modifications",
        search="_search_has_pending_modifications",
    )

    @api.depends("modification_ids.sent", "modification_ids.is_internal")
    def _compute_pending_modifications(self):
        for rec in self:
            pending = rec.modification_ids.filtered(
                lambda m: not m.sent and not m.is_internal
            )
            rec.pending_modification_count = len(pending)
            rec.has_pending_modifications = bool(pending)

    def _search_has_pending_modifications(self, operator, value):
        if operator == "=" and value:
            return [
                ("modification_ids.sent", "=", False),
                ("modification_ids.is_internal", "=", False),
            ]
        return []

    def action_send_pending_modifications(self):
        for rec in self:
            pending = rec.modification_ids.filtered(
                lambda m: not m.sent and not m.is_internal
            )
            if pending:
                template = self.env.ref(
                    "contract_management.mail_template_contract_modification_grouped",
                    raise_if_not_found=False,
                )
                if template:
                    # Send email and post in chatter
                    rec.message_post_with_source(
                        template,
                        subtype_xmlid="mail.mt_comment",
                    )
                pending.write({"sent": True})

    @api.onchange("contract_template_id")
    def _onchange_contract_template_id(self):
        res = super()._onchange_contract_template_id()
        if (
            self.contract_template_id
            and self.contract_template_id.analytic_distribution
        ):
            self.analytic_distribution = self.contract_template_id.analytic_distribution
            self._onchange_analytic_distribution_header()
        return res

    @api.onchange("analytic_distribution")
    def _onchange_analytic_distribution_header(self):
        """Propaga la distribución analítica de la cabecera a todas las líneas."""
        if self.analytic_distribution:
            for line in self.contract_line_ids:
                line.analytic_distribution = self.analytic_distribution
            for line in self.contract_line_fixed_ids:
                line.analytic_distribution = self.analytic_distribution
