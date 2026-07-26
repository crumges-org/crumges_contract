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
        "views/contract_dashboard_views.xml",
        "views/contract_views.xml",
        "views/contract_menu.xml",
        "views/contract_modification_views.xml",
        "views/res_config_settings_views.xml",
        "views/account_move_views.xml",
        "views/sale_order_views.xml"
    ],
    "installable": True,
    "application": True,
}
