const ACTIVE_CLASSES = [
  "active",
  "border-blue-500",
  "text-blue-600",
  "dark:text-blue-400",
  "dark:border-blue-400",
];

const INACTIVE_CLASSES = [
  "border-transparent",
  "text-gray-500",
  "dark:text-gray-400",
];

export class AtTabManager extends HTMLElement {
  constructor() {
    super();
    this._onClick = this._onClick.bind(this);
    this._onDropdownChange = this._onDropdownChange.bind(this);
  }

  connectedCallback() {
    // Cache elements within the manager; assumes buttons/panels are children
    this._buttons = Array.from(this.querySelectorAll(".tab-button"));
    this._panels = Array.from(this.querySelectorAll(".tab-content"));
    this._mobileDropdown = this.querySelector("#mobile-tab-selector");
    
    this._buttons.forEach((btn) => btn.addEventListener("click", this._onClick));
    
    // Listen for mobile dropdown changes
    if (this._mobileDropdown) {
      this._mobileDropdown.addEventListener("change", this._onDropdownChange);
    }

    const preset = this.getAttribute("active");
    const activeButton = this._buttons.find((btn) => btn.classList.contains("active"));
    const initialTab = preset || activeButton?.dataset.tab || this._buttons[0]?.dataset.tab;
    if (initialTab) {
      this.setActive(initialTab, false);
    }
  }

  disconnectedCallback() {
    this._buttons?.forEach((btn) => btn.removeEventListener("click", this._onClick));
    if (this._mobileDropdown) {
      this._mobileDropdown.removeEventListener("change", this._onDropdownChange);
    }
  }

  setActive(tabName, fromUser = false) {
    if (!tabName) return;

    if (!this._buttons || !this._panels) {
      // If somehow invoked before connectedCallback, hydrate on demand
      this._buttons = Array.from(this.querySelectorAll(".tab-button"));
      this._panels = Array.from(this.querySelectorAll(".tab-content"));
    }

    this._buttons.forEach((btn) => {
      const isActive = btn.dataset.tab === tabName;
      this._toggleClasses(btn, isActive);
    });

    this._panels.forEach((panel) => {
      const isActive = panel.id === `${tabName}-tab`;
      panel.classList.toggle("hidden", !isActive);
      panel.classList.toggle("active", isActive);
    });

    // Update mobile dropdown to match (without triggering change event)
    if (this._mobileDropdown && this._mobileDropdown.value !== tabName) {
      this._mobileDropdown.value = tabName;
    }

    if (fromUser && typeof window.switchTabPython !== "undefined") {
      window.switchTabPython(tabName);
    }

    this.dispatchEvent(
      new CustomEvent("tab-change", {
        bubbles: true,
        detail: { tab: tabName },
      })
    );
  }

  _onDropdownChange(event) {
    const tab = event.target.value;
    this.setActive(tab, true);
  }

  _onClick(event) {
    const tab = event.currentTarget?.dataset?.tab;
    this.setActive(tab, true);
  }

  _toggleClasses(el, isActive) {
    ACTIVE_CLASSES.forEach((cls) => el.classList.toggle(cls, isActive));
    INACTIVE_CLASSES.forEach((cls) => el.classList.toggle(cls, !isActive));
  }
}

customElements.define("at-tab-manager", AtTabManager);
