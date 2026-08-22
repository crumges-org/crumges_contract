from odoo import fields, models


class ContractDashboardTrend(models.Model):
    _name = "contract.dashboard.trend"
    _description = "Tendencias y KPIs del Tablero"
    _order = "metric_type, sequence, id"

    name = fields.Char(string="Leyenda", required=True, translate=True)
    sequence = fields.Integer(
        string="Secuencia", default=10, help="Orden de evaluación (menor a mayor)."
    )

    metric_type = fields.Selection(
        [
            ("active_contracts", "Contratos Activos"),
            ("total_revenue", "Valor Total (Ingresos)"),
            ("expiring_soon", "Próximos a Vencer"),
        ],
        string="Tarjeta a evaluar",
        required=True,
    )

    comparison_period = fields.Selection(
        [("7", "Últimos 7 días"), ("15", "Últimos 15 días"), ("30", "Últimos 30 días")],
        string="Período de Comparación",
        required=True,
        default="30",
    )

    operator = fields.Selection(
        [
            (">=", "Mayor o igual a (>=)"),
            ("<=", "Menor o igual a (<=)"),
            ("==", "Igual a (==)"),
            (">", "Mayor a (>)"),
            ("<", "Menor a (<)"),
        ],
        string="Condición",
        required=True,
        default=">=",
    )

    percentage = fields.Float(
        string="Porcentaje Umbral (%)", required=True, default=0.0
    )

    color = fields.Selection(
        [
            ("text-success", "Verde (Positivo)"),
            ("text-danger", "Rojo (Negativo)"),
            ("text-warning", "Naranja (Alerta)"),
            ("text-info", "Celeste (Informativo)"),
            ("text-dark", "Negro (Neutral)"),
        ],
        string="Color del Porcentaje",
        required=True,
        default="text-success",
    )

    details = fields.Text(
        string="Detalles (Tooltip)",
        translate=True,
        help="Texto que aparecerá al pasar el mouse sobre el porcentaje.",
    )

    active = fields.Boolean(default=True)

    def evaluate_trend(self, actual_growth):
        """Evalúa si el porcentaje actual de crecimiento cumple la regla de este registro."""
        self.ensure_one()
        if self.operator == ">=":
            return actual_growth >= self.percentage
        elif self.operator == "<=":
            return actual_growth <= self.percentage
        elif self.operator == "==":
            return actual_growth == self.percentage
        elif self.operator == ">":
            return actual_growth > self.percentage
        elif self.operator == "<":
            return actual_growth < self.percentage
        return False
