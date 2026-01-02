import type { AtDropdownElement, DropdownSelectEventDetail } from '../../types/dom';
import type { DropdownOption } from '../../types/pyscript';

/**
 * AtDropdown - Custom dropdown component with filtering and keyboard navigation
 * 
 * Usage:
 * <at-dropdown id="my-dropdown" label="Select Option" placeholder="Search..."></at-dropdown>
 * 
 * Events:
 * - 'select': Fired when an option is selected (CustomEvent with DropdownOption detail)
 * - 'change': Fired when the value changes
 */
export class AtDropdown extends HTMLElement implements AtDropdownElement {
  private _options: DropdownOption[] = [];
  private _selected: DropdownOption | null = null;
  private _inputEl?: HTMLInputElement;
  private _listEl?: HTMLDivElement;
  private _onDocumentClick: (event: MouseEvent) => void;
  private _initialized: boolean = false;

  constructor() {
    super();
    this._onDocumentClick = this._handleDocumentClick.bind(this);
  }

  connectedCallback(): void {
    if (this._initialized) return;
    this._initialized = true;
    this.style.display = 'block';
    this._build();
    document.addEventListener('click', this._onDocumentClick);
  }

  disconnectedCallback(): void {
    document.removeEventListener('click', this._onDocumentClick);
  }

  set options(list: DropdownOption[]) {
    this._options = Array.isArray(list) ? list : [];
    this._render();
  }

  get options(): DropdownOption[] {
    return this._options;
  }

  get value(): string {
    return this._inputEl?.value || '';
  }

  set value(val: string) {
    if (this._inputEl) {
      this._inputEl.value = val || '';
    }
  }

  get selectedId(): string | null {
    return this._selected?.id || null;
  }

  get selectedOption(): DropdownOption | null {
    return this._selected;
  }

  clear(): void {
    this._selected = null;
    this.value = '';
    this._render();
    this.dispatchEvent(new Event('change', { bubbles: true }));
  }

  open(): void {
    this._listEl?.classList.remove('hidden');
    this._render(this.value);
  }

  close(): void {
    this._listEl?.classList.add('hidden');
  }

  selectById(optionId: string): void {
    const match = this._options.find((opt) => opt.id === optionId);
    if (match) {
      this._select(match, false);
    }
  }

  private _filter(): void {
    this._render(this.value);
    this.open();
  }

  private _select(option: DropdownOption, fireEvent: boolean): void {
    this._selected = option;
    this.value = option.text;
    this.close();

    if (fireEvent) {
      this.dispatchEvent(
        new CustomEvent<DropdownSelectEventDetail>('select', {
          bubbles: true,
          detail: option as DropdownSelectEventDetail,
        })
      );
      this.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }

  private _handleDocumentClick(event: MouseEvent): void {
    if (!this.contains(event.target as Node)) {
      this.close();
    }
  }

  private _build(): void {
    const label = this.getAttribute('label') || '';
    const placeholder = this.getAttribute('placeholder') || '';
    const disabled = this.hasAttribute('disabled');

    this.innerHTML = `
      <label data-part="label" class="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-200">${label}</label>
      <div class="relative">
        <input
          data-part="input"
          type="text"
          autocomplete="off"
          ${disabled ? 'disabled' : ''}
          placeholder="${placeholder}"
          class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed dark:bg-gray-800 dark:border-gray-700 dark:text-gray-100 dark:placeholder:text-gray-500"
        />
        <div data-part="list" class="absolute left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-64 overflow-y-auto z-30 hidden"></div>
      </div>
    `;

    this._inputEl = this.querySelector('[data-part="input"]') as HTMLInputElement;
    this._listEl = this.querySelector('[data-part="list"]') as HTMLDivElement;

    if (this.hasAttribute('value')) {
      this.value = this.getAttribute('value') || '';
    }

    if (this._inputEl) {
      this._inputEl.addEventListener('input', () => this._filter());
      this._inputEl.addEventListener('focus', () => this.open());
      this._inputEl.addEventListener('keydown', (event: KeyboardEvent) => {
        if (event.key === 'Escape') {
          this.close();
        }
      });
    }
  }

  private _renderEmptyState(): void {
    if (!this._listEl) return;
    
    const empty = document.createElement('div');
    empty.className = 'px-3 py-2 text-sm text-gray-500 dark:text-gray-400';
    empty.textContent = this.getAttribute('empty-text') || 'No results';
    this._listEl.appendChild(empty);
  }

  private _renderListItem(option: DropdownOption): void {
    if (!this._listEl) return;
    
    const isSelected = this._selected && this._selected.id === option.id;
    const item = document.createElement('button');
    item.type = 'button';
    item.className = [
      'w-full text-left px-3 py-2 text-sm transition-colors',
      'hover:bg-blue-50 dark:hover:bg-gray-700',
      'focus:outline-none focus:bg-blue-100 dark:focus:bg-gray-700',
      isSelected ? 'bg-blue-100 text-blue-700 dark:bg-gray-700 dark:text-gray-100' : 'text-gray-800 dark:text-gray-100'
    ].join(' ');
    item.textContent = option.text;
    item.setAttribute('role', 'option');
    if (isSelected) {
      item.setAttribute('aria-selected', 'true');
    }
    item.addEventListener('click', () => this._select(option, true));
    this._listEl.appendChild(item);
  }

  private _renderList(filtered: DropdownOption[]): void {
    if (!this._listEl) return;
    
    this._listEl.innerHTML = '';

    if (!filtered.length) {
      this._renderEmptyState();
      return;
    }

    filtered.forEach((option) => this._renderListItem(option));
  }

  private _render(filterValue: string = ''): void {
    if (!this._listEl) return;

    const normalized = filterValue.trim().toLowerCase();
    const filtered = normalized
      ? this._options.filter((opt) => opt.text.toLowerCase().includes(normalized))
      : this._options;

    this._renderList(filtered);
  }
}

customElements.define('at-dropdown', AtDropdown);
