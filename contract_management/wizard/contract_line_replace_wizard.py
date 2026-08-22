from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ContractLineReplaceWizard(models.TransientModel):
    _name = "contract.line.replace.wizard"
    _inherits = {"generic.variant.wizard": "generic_wizard_id"}
    _description = "Asistente para Reemplazar Línea de Contrato"

    generic_wizard_id = fields.Many2one(
        "generic.variant.wizard", required=True, ondelete="cascade"
    )
    line_id = fields.Many2one(
        "contract.line", string="Línea a Reemplazar", required=True, readonly=True
    )
    contract_id = fields.Many2one("contract.contract", related="line_id.contract_id")

    # Old data display - Not related to avoid UI wiping them out when line is virtual
    old_product_name = fields.Char(string="Producto Actual", readonly=True)
    old_quantity = fields.Float(string="Cantidad Actual", readonly=True)

    # New data
    date_change = fields.Date(
        string="Fecha Efectiva del Cambio",
        default=fields.Date.context_today,
        required=True,
        help="Fecha en que el nuevo plan entra en vigencia. El plan anterior se cortará un día antes.",
    )
    name = fields.Char("Descripción")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if (
            "line_id" not in res
            and self.env.context.get("active_model") == "contract.line"
            and self.env.context.get("active_id")
        ):
            res["line_id"] = self.env.context.get("active_id")
        if res.get("line_id"):
            try:
                line_id_int = int(res["line_id"])
                line = self.env["contract.line"].browse(line_id_int)
                if line.exists():
                    import logging

                    _logger = logging.getLogger(__name__)

                    if line.product_id:
                        res["old_product_name"] = line.product_id.display_name
                        res["product_template_id"] = line.product_id.product_tmpl_id.id
                    elif (
                        hasattr(line, "product_template_id")
                        and line.product_template_id
                    ):
                        res["old_product_name"] = line.product_template_id.display_name
                        res["product_template_id"] = line.product_template_id.id
                    else:
                        res["old_product_name"] = line.name or "Línea sin producto"
                        res["product_template_id"] = self.env.context.get(
                            "default_product_template_id"
                        )

                    res["old_quantity"] = line.quantity

                    _logger.info("RES DICT BEFORE RETURN: %s", res)
                    # Pre-seleccionar los mismos atributos que ya tenía
                    lines = []
                    product = line.product_id
                    for ptal in product.product_tmpl_id.attribute_line_ids:
                        default_val = False
                        # Buscar el valor que tenía este atributo en el producto viejo
                        ptav = product.product_template_attribute_value_ids.filtered(
                            lambda v: v.attribute_id.id == ptal.attribute_id.id
                        )
                        if ptav:
                            default_val = ptav.product_attribute_value_id.id
                        elif len(ptal.value_ids) == 1:
                            default_val = ptal.value_ids[0].id

                        lines.append(
                            (
                                0,
                                0,
                                {
                                    "attribute_id": ptal.attribute_id.id,
                                    "value_id": default_val,
                                },
                            )
                        )
                    res["line_ids"] = lines
            except ValueError:
                pass
        return res

    # Options
    force_legend = fields.Boolean(
        string="Forzar fechas exactas en leyenda",
        default=True,
        help="Si está marcado, se añadirá explícitamente el periodo exacto al nombre de las líneas (vieja y nueva) para mayor claridad.",
    )

    @api.onchange("product_template_id")
    def _onchange_product_template_id_wizard(self):
        if not self.product_template_id:
            self.line_ids = [(5, 0, 0)]
            return

        current_attr_ids = set(self.line_ids.mapped("attribute_id.id"))
        tmpl_attr_ids = set(
            self.product_template_id.attribute_line_ids.mapped("attribute_id.id")
        )

        if current_attr_ids == tmpl_attr_ids:
            return

        self.line_ids = [(5, 0, 0)]
        lines = []
        for ptal in self.product_template_id.attribute_line_ids:
            default_val = False
            if len(ptal.value_ids) == 1:
                default_val = ptal.value_ids[0].id

            lines.append(
                (
                    0,
                    0,
                    {
                        "attribute_id": ptal.attribute_id.id,
                        "value_id": default_val,
                    },
                )
            )
        self.line_ids = lines

    @api.onchange("line_ids", "product_template_id")
    def _onchange_compute_product_id_and_price(self):
        for wizard in self:
            # Calcular Product ID
            wizard.product_id = False
            if wizard.product_template_id and wizard.line_ids:
                selected_value_ids = wizard.line_ids.mapped("value_id").ids
                if len(selected_value_ids) == len(
                    wizard.product_template_id.attribute_line_ids
                ):
                    for variant in wizard.product_template_id.product_variant_ids:
                        variant_value_ids = (
                            variant.product_template_attribute_value_ids.mapped(
                                "product_attribute_value_id"
                            ).ids
                        )
                        if set(selected_value_ids) == set(variant_value_ids):
                            wizard.product_id = variant.id
                            break

            # Calcular Price
            if wizard.product_id:
                wizard.price = wizard.product_id.list_price
            elif wizard.product_template_id:
                price = wizard.product_template_id.list_price
                for line in wizard.line_ids:
                    if line.value_id:
                        price += line.price_extra
                wizard.price = price
            else:
                wizard.price = 0.0

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.price = self.product_id.list_price

    def action_replace_line(self):
        self.ensure_one()
        line = self.line_id
        contract = line.contract_id

        if not self.product_id:
            raise ValidationError(
                _(
                    "Por favor, asegúrate de seleccionar todos los atributos para formar una variante válida del Nuevo Servicio."
                )
            )

        if line.date_end and line.date_end <= self.date_change:
            raise UserError(
                _(
                    "La línea actual ya finaliza antes o en la misma fecha de efectividad seleccionada."
                )
            )

        if line.date_start and self.date_change <= line.date_start:
            # If the line was created on the same day it's being replaced, just set date_end = date_start
            # to avoid Odoo ValidationError where date_start > date_end
            new_date_end = line.date_start
        else:
            new_date_end = self.date_change - timedelta(days=1)

        new_line_vals = line.copy_data()[0]
        new_next_date = self.date_change
        if (
            contract.recurring_next_date
            and contract.recurring_next_date > self.date_change
        ):
            new_next_date = contract.recurring_next_date

        new_line_vals.update(
            {
                "date_start": self.date_change,
                "product_id": self.product_id.id,
                "quantity": self.quantity,
                "price_unit": self.price,
                "replaces_line_id": line.id,
            }
        )

        # Eliminar fechas copiadas que puedan dar conflicto con las validaciones de OCA contract
        # Al copiar la línea vieja, vienen campos calculados que confunden al ORM al crear la nueva
        for field in [
            "date_end",
            "last_date_invoiced",
            "next_period_date_end",
            "next_period_date_start",
            "recurring_next_date",
        ]:
            if field in new_line_vals:
                new_line_vals.pop(field)

        # Manejo de leyenda forzada
        if self.force_legend:
            old_start = (
                line.date_start.strftime("%d/%m/%Y") if line.date_start else "..."
            )
            old_end = new_date_end.strftime("%d/%m/%Y")

        # Limpiar posible leyenda vieja en el nombre actual
        old_name = line.name or line.product_id.display_name or ""
        import re

        old_name_clean = re.sub(
            r" - .*?(#START# al #END#|#INVOICEMONTHNAME#|desde .*)$", "", old_name
        )
        old_name_clean = re.sub(r" \(desde .*\)$", "", old_name_clean).strip()

        # Build variant description for new product
        variant_desc = []
        for l in self.line_ids:
            if l.value_id:
                variant_desc.append(f"{l.attribute_id.name}: {l.value_id.name}")

        custom_name = (
            self.product_template_id.name or self.product_id.display_name or ""
        )
        if variant_desc:
            custom_name = f"{custom_name} ({', '.join(variant_desc)})"

        new_name_clean = self.name or custom_name

        # Manejo de leyenda forzada
        if self.force_legend:
            old_start = (
                line.date_start.strftime("%d/%m/%Y") if line.date_start else "..."
            )
            old_end = new_date_end.strftime("%d/%m/%Y")

            line.name = f"{old_name_clean} (desde {old_start} al {old_end})"

            new_start = self.date_change.strftime("%d/%m/%Y")
            new_line_vals["name"] = f"{new_name_clean} (desde {new_start})"
        else:
            new_line_vals["name"] = new_name_clean

        # 2. Cortar la línea vieja
        line.date_end = new_date_end

        # 3. Crear la nueva línea
        new_line = self.env["contract.line"].create(new_line_vals)

        # 4. Actualizar link en la línea vieja
        line.replaced_by_line_id = new_line.id

        # 5. Generar la modificación a través del motor de reglas
        rule = self.env["contract.modification.rule"].search(
            [("model_id.model", "=", "contract.line"), ("action_type", "=", "replace")],
            limit=1,
        )

        old_product = old_name_clean
        new_product = new_name_clean
        date_str = self.date_change.strftime("%d/%m/%Y")

        if rule and rule.message_template:
            msg = str(rule.message_template)
            msg = msg.replace("${old_product}", old_product)
            msg = msg.replace("${new_product}", new_product)
            msg = msg.replace("${date}", date_str)
            msg = msg.replace("${old_quantity}", str(line.quantity))
            msg = msg.replace("${new_quantity}", str(new_line.quantity))
            is_internal = rule.is_internal
            sent_value = True if is_internal else False
        else:
            msg = f"Se reemplazó la línea de {old_product} por {new_product} a partir del {date_str}."
            is_internal = False
            sent_value = False

        self.env["contract.modification"].with_context(
            bypass_modification_send=True
        ).create(
            {
                "contract_id": contract.id,
                "date": fields.Date.context_today(self),
                "description": msg,
                "is_internal": is_internal,
                "sent": sent_value,
            }
        )

        return {"type": "ir.actions.client", "tag": "reload"}
