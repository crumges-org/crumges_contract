/* eslint-env browser */
/* eslint-disable */
/** @odoo-module **/

import {KanbanController} from "@web/views/kanban/kanban_controller";
import {kanbanView} from "@web/views/kanban/kanban_view";
import {registry} from "@web/core/registry";
import {Component, onWillStart} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";

export class ContractDashboardHeader extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = {
            total_active: 0,
            total_revenue: 0,
            total_expiring: 0,
            currency_symbol: "$",
            trends: {
                active_contracts: null,
                total_revenue: null,
                expiring_soon: null,
            },
            state_revenue: {
                draft: 0,
                in_progress: 0,
                paused: 0,
            },
            states: {
                draft: 0,
                in_progress: 0,
                paused: 0,
                done: 0,
                cancelled: 0,
            },
            expiring: {
                d7: {count: 0, domain: []},
                d15: {count: 0, domain: []},
                d30: {count: 0, domain: []},
                d365: {count: 0, domain: []},
            },
        };
        onWillStart(async () => {
            const result = await this.orm.call(
                "contract.contract",
                "get_global_dashboard_stats",
                []
            );
            Object.assign(this.state, result);
        });
    }

    async openStateContracts(stateStr) {
        let context = {};
        let stateName = {
            draft: "Borradores",
            in_progress: "En Curso",
            paused: "Pausados",
            done: "Finalizados",
            cancelled: "Cancelados",
        }[stateStr];

        if (stateStr) {
            context[`search_default_filter_state_${stateStr}`] = 1;
        }

        await this.action.doAction({
            type: "ir.actions.act_window",
            name: `Contratos ${stateName}`,
            res_model: "contract.contract",
            view_mode: "kanban,list,calendar,activity,form",
            views: [
                [false, "kanban"],
                [false, "list"],
                [false, "calendar"],
                [false, "activity"],
                [false, "form"],
            ],
            context: context,
            target: "current",
        });
    }

    async openContracts(interval) {
        const data = this.state.expiring[interval];
        if (!data || data.count === 0) return;

        let context = {};
        if (interval) {
            context[`search_default_filter_expiring_${interval}`] = 1;
        }

        await this.action.doAction({
            type: "ir.actions.act_window",
            name: "Contratos por Vencer",
            res_model: "contract.contract",
            view_mode: "kanban,list,calendar,activity,form",
            views: [
                [false, "kanban"],
                [false, "list"],
                [false, "calendar"],
                [false, "activity"],
                [false, "form"],
            ],
            context: context,
            target: "current",
        });
    }
}
ContractDashboardHeader.template = "contract_management.DashboardHeader";

export class ContractKanbanController extends KanbanController {}
ContractKanbanController.template = "contract_management.KanbanView";
ContractKanbanController.components = {
    ...KanbanController.components,
    ContractDashboardHeader,
};

export const contractKanbanView = {
    ...kanbanView,
    Controller: ContractKanbanController,
};

registry.category("views").add("contract_dashboard_kanban", contractKanbanView);
