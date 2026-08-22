import odoo
from odoo import SUPERUSER_ID, api

odoo.tools.config.parse_config(["-c", "/opt/odoo/auto/odoo.conf", "-d", "devel"])
registry = odoo.registry("devel")
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    records = (
        env["contract.template"]
        .with_context(active_test=False)
        .search([("active", "=", False)])
    )
    import logging

    logger = logging.getLogger(__name__)
    logger.info("COUNT INACTIVE: %s", len(records))
    logger.info("NAMES: %s", [r.name for r in records[:3]])
