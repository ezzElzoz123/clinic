/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

class ClinicSidebar extends Component {
    static template = "clinic.ClinicSidebar";
}

registry.category("systray").add("clinic.sidebar", {
    Component: ClinicSidebar,
    sequence: 1,
});