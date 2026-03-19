// static/src/js/dark_mode_toggle.js
/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";

class DarkModeToggle extends Component {
    static template = "clinic.DarkModeToggle";

    setup() {
        this.state = useState({
            dark: localStorage.getItem("clinic_dark_mode") === "1"
        });
        // طبّق عند التحميل
        this._apply(this.state.dark);
    }

    toggle() {
        this.state.dark = !this.state.dark;
        localStorage.setItem("clinic_dark_mode", this.state.dark ? "1" : "0");
        this._apply(this.state.dark);
    }

    _apply(isDark) {
        document.body.classList.toggle("dark-mode", isDark);
    }
}

// اضيفه في systray (الـ icons اليمين في الـ navbar)
registry.category("systray").add("clinic.dark_mode_toggle", {
    Component: DarkModeToggle,
    sequence: 99,
});