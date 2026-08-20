import odoo
from odoo import api, SUPERUSER_ID
odoo.tools.config.parse_config(['-c', '/opt/odoo/auto/odoo.conf', '-d', 'devel'])
registry = odoo.registry('devel')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    records = env['contract.template'].with_context(active_test=False).search([('active', '=', False)])
    print("COUNT INACTIVE:", len(records))
    print("NAMES:", [r.name for r in records[:3]])
