import type { AtTabManagerElement, TabChangeEventDetail } from '../../types/dom';

const ACTIVE_CLASSES = [
  "active",
  "border-blue-500",
  "text-blue-600",
  "dark:text-blue-400",
  "dark:border-blue-400",
] as const;

const INACTIVE_CLASSES = [
  "border-transparent",
  "text-gray-500",
  "dark:text-gray-400",
] as const;

/**
 * AtTabManager - Custom tab navigation component
 * 
 * Usage:
 * <at-tab-manager active="dependency-mapper">
 *   <button class="tab-button" data-tab="tab1">Tab 1</button>
 *   <div class="tab-content" id="tab1-tab">Content 1</div>
 * </at-tab-manager>
 * 
 * Events:
 * - 'tab-change': Fired when active tab changes (CustomEvent with tab name in detail)
 */
export class AtTabManager extends HTMLElement implements AtTabManagerElement {
  private _buttons?: HTMLElement[];
  private _panels?: HTMLElement[];
  private _mobileDropdown?: HTMLSelectElement | null;

  constructor() {
    super();
  }

  connectedCallback(): void {
    // Cache elements within the manager; assumes buttons/panels are children
    this._buttons = Array.from(this.querySelectorAll<HTMLElement>(".tab-button"));
    this._panels = Array.from(this.querySelectorAll<HTMLElement>(".tab-content"));
    this._mobileDropdown = this.querySelector<HTMLSelectElement>("#mobile-tab-selector");
    
    this._buttons.forEach((btn) => btn.addEventListener("click", (e) => this._onClick(e)));
    
    // Listen for mobile dropdown changes
    if (this._mobileDropdown) {
      this._mobileDropdown.addEventListener("change", (e) => this._onDropdownChange(e));
    }

    const preset = this.getAttribute("active");
    const activeButton = this._buttons.find((btn) => btn.classList.contains("active"));
    const initialTab = preset || activeButton?.dataset.tab || this._buttons[0]?.dataset.tab;
    if (initialTab) {
      this.setActive(initialTab, false);
    }
  }

  disconnectedCallback(): void {
    // Event listeners with arrow functions don't need explicit removal
    // as they're garbage collected with the element
  }

  /**
   * Set the active tab
   * @param tabName - The name of the tab to activate
   * @param emit - Whether to emit tab-change event and call Python callback
   */
  setActive(tabName: string, emit: boolean = false): void {
    if (!tabName) return;

    if (!this._buttons || !this._panels) {
      // If somehow invoked before connectedCallback, hydrate on demand
      this._buttons = Array.from(this.querySelectorAll<HTMLElement>(".tab-button"));
      this._panels = Array.from(this.querySelectorAll<HTMLElement>(".tab-content"));
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

    if (emit && typeof window.switchTabPython !== "undefined") {
      window.switchTabPython(tabName);
    }

    this.dispatchEvent(
      new CustomEvent<TabChangeEventDetail>("tab-change", {
        bubbles: true,
        detail: { tab: tabName },
      })
    );
  }

  /**
   * Get the currently active tab name
   * @returns The active tab name or null if none active
   */
  getActive(): string | null {
    const activeButton = this._buttons?.find((btn) => btn.classList.contains("active"));
    return activeButton?.dataset.tab || null;
  }

  private _onDropdownChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    const tab = target.value;
    this.setActive(tab, true);
  }

  private _onClick(event: MouseEvent): void {
    const currentTarget = event.currentTarget as HTMLElement;
    const tab = currentTarget?.dataset?.tab;
    if (tab) {
      this.setActive(tab, true);
    }
  }

  private _toggleClasses(el: HTMLElement, isActive: boolean): void {
    ACTIVE_CLASSES.forEach((cls) => el.classList.toggle(cls, isActive));
    INACTIVE_CLASSES.forEach((cls) => el.classList.toggle(cls, !isActive));
  }
}

// Extend window interface for Python callback
declare global {
  interface Window {
    switchTabPython?(tabName: string): void;
  }
}

customElements.define("at-tab-manager", AtTabManager);
