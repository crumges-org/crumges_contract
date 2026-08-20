from odoo import api, fields, models
from datetime import datetime

class ContractModificationRule(models.Model):
    _name = 'contract.modification.rule'
    _description = 'Contract Modification Rule'

    name = fields.Char(string='Rule Name', required=True)
    model_id = fields.Many2one(
        'ir.model', 
        string='Model', 
        required=True,
        ondelete='cascade',
        domain="[('model', 'in', ['contract.contract', 'contract.line'])]"
    )
    field_id = fields.Many2one(
        'ir.model.fields', 
        string='Field to Audit',
        ondelete='cascade',
        domain="[('model_id', '=', model_id)]"
    )
    action_type = fields.Selection([
        ('create', 'Creation'),
        ('write', 'Modification'),
        ('unlink', 'Deletion')
    ], string='Action', required=True)
    
    message_template = fields.Text(
        string='Message Template', 
        required=True,
        help="Use variables like ${object.name}, ${old_value}, ${new_value}."
    )

    @api.model
    def evaluate_rules(self, record, action, vals, old_vals=None):
        if not old_vals:
            old_vals = {}
            
        rules = self.search([
            ('model_id.model', '=', record._name),
            ('action_type', '=', action)
        ])
        
        for rule in rules:
            field_name = rule.field_id.name
            if not field_name:
                continue
                
            if action == 'write':
                if field_name not in vals:
                    continue
                new_val = vals[field_name]
                old_val = old_vals.get(field_name)
                if new_val == old_val:
                    continue
            else:
                new_val = record[field_name] if field_name in record else False
                old_val = False

            def get_display(val, field):
                if val is False or val is None:
                    return "Empty"
                if field.type in ['many2one', 'reference']:
                    if isinstance(val, int):
                        try:
                            rel_record = self.env[field.comodel_name].browse(val)
                            return rel_record.display_name or str(val)
                        except:
                            return str(val)
                    elif hasattr(val, 'display_name'):
                        return val.display_name or str(val)
                elif field.type == 'selection':
                    selection = dict(field._description_selection(self.env))
                    return str(selection.get(val, val))
                elif field.type in ['monetary', 'float']:
                    currency = False
                    if 'currency_id' in record and record.currency_id:
                        currency = record.currency_id
                    elif hasattr(record, 'contract_id') and record.contract_id and record.contract_id.company_id.currency_id:
                        currency = record.contract_id.company_id.currency_id
                    elif 'company_id' in record and record.company_id and record.company_id.currency_id:
                        currency = record.company_id.currency_id
                        
                    if currency:
                        try:
                            return f"{currency.symbol} {float(val):.2f}"
                        except:
                            pass
                return str(val)

            field_def = record._fields.get(field_name)
            if not field_def:
                continue
                
            formatted_old = get_display(old_val, field_def)
            formatted_new = get_display(new_val, field_def)

            msg = rule.message_template or ''
            msg = msg.replace('${object.name}', record.display_name or '')
            msg = msg.replace('${old_value}', formatted_old)
            msg = msg.replace('${new_value}', formatted_new)

            contract_id = record.id if record._name == 'contract.contract' else record.contract_id.id

            if contract_id:
                # Write to OCA native model to show in Modifications tab and portal
                self.env['contract.modification'].create({
                    'contract_id': contract_id,
                    'date': fields.Date.context_today(self),
                    'description': msg,
                })

class ContractModificationLog(models.Model):
    _name = 'contract.modification.log'
    _description = 'Contract Modification Log'
    _order = 'create_date desc'

    contract_id = fields.Many2one('contract.contract', string='Contract', ondelete='cascade', index=True)
    rule_id = fields.Many2one('contract.modification.rule', string='Applied Rule')
    message = fields.Text(string='Message')
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
