{
    "name": "Contract Management App",
    "version": "18.0.1.0.0",
    "author": "Crumges",
    "website": "https://crumges.com",
    "category": "Sales/Contracts",
    "depends": ["contract", "contract_sale_generation", "web_timeline", "base_setup"],
    "data": [
        "security/contract_groups.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence.xml",
        "data/dashboard_data.xml",
        "data/trend_data.xml",
        "views/contract_category_views.xml",
        "views/contract_views.xml",
        "views/contract_menu.xml",
        "views/contract_trend_views.xml",
        "views/contract_modification_views.xml",
        "views/res_config_settings_views.xml",
        "views/account_move_views.xml",
        "views/sale_order_views.xml",
        "views/contract_portal_templates.xml",
        "views/contract_report_templates.xml",
        "data/mail_template_data.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "contract_management/static/src/xml/contract_dashboard.xml",
            "contract_management/static/src/js/contract_dashboard.js"
        ]
    },
    "installable": True,
    "application": True,
}
