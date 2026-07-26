from odoo import api, fields, models
from datetime import datetime

class ContractModificationRule(models.Model):
    _name = 'contract.modification.rule'
    _description = 'Regla de Modificación de Contrato'

    name = fields.Char(string='Nombre de Regla', required=True)
    model_id = fields.Many2one(
        'ir.model', 
        string='Modelo', 
        required=True,
        ondelete='cascade',
        domain="[('model', 'in', ['contract.contract', 'contract.line'])]"
    )
    field_id = fields.Many2one(
        'ir.model.fields', 
        string='Campo a Auditar',
        ondelete='cascade',
        domain="[('model_id', '=', model_id)]"
    )
    action_type = fields.Selection([
        ('create', 'Alta (Creación)'),
        ('write', 'Modificación (Edición)'),
        ('unlink', 'Baja (Eliminación)')
    ], string='Acción', required=True)
    
    message_template = fields.Text(
        string='Plantilla de Mensaje', 
        required=True,
        help="Use variables como ${object.name}, ${old_value}, ${new_value}. Para objetos relacionales puede usar ${object.product_id.name}"
    )

class ContractModificationLog(models.Model):
    _name = 'contract.modification.log'
    _description = 'Registro de Modificación de Contrato'
    _order = 'create_date desc'

    contract_id = fields.Many2one('contract.contract', string='Contrato', ondelete='cascade', index=True)
    rule_id = fields.Many2one('contract.modification.rule', string='Regla Aplicada')
    message = fields.Text(string='Mensaje')
    date = fields.Datetime(string='Fecha', default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user)
