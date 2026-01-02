/**
 * Type definitions for custom web components
 */

import type { DropdownOption } from './pyscript';

// Custom element interfaces
export interface AtDropdownElement extends HTMLElement {
  options: DropdownOption[];
  value: string;
  selectedId: string | null;
  selectedOption: DropdownOption | null;
  clear(): void;
  open(): void;
  close(): void;
  selectById(optionId: string): void;
}

export interface AtTabManagerElement extends HTMLElement {
  setActive(tabName: string, emit?: boolean): void;
  getActive(): string | null;
}

export interface AtThemeToggleElement extends HTMLElement {
  // Theme toggle custom element methods (if any)
}

// CustomEvent detail types for component events
export interface DropdownSelectEventDetail extends DropdownOption {
  // Extends DropdownOption with event-specific fields
}

export interface TabChangeEventDetail {
  tab: string;
  previous?: string;
}

// Extend the global HTMLElementTagNameMap for proper typing
declare global {
  interface HTMLElementTagNameMap {
    'at-dropdown': AtDropdownElement;
    'at-tab-manager': AtTabManagerElement;
    'at-theme-toggle': AtThemeToggleElement;
  }

  // Add custom event types
  interface DocumentEventMap {
    'tab-change': CustomEvent<TabChangeEventDetail>;
  }

  interface HTMLElementEventMap {
    'select': CustomEvent<DropdownSelectEventDetail>;
  }
}

export {};
