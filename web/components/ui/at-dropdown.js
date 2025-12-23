export class AtDropdown extends HTMLElement {
  constructor() {
    super();
    this._options = [];
    this._selected = null;
    this._onDocumentClick = this._handleDocumentClick.bind(this);
  }

  connectedCallback() {
    if (this._initialized) return;
    this._initialized = true;
    this.style.display = 'block';
    this._build();
    document.addEventListener('click', this._onDocumentClick);
  }

  disconnectedCallback() {
    document.removeEventListener('click', this._onDocumentClick);
  }

  set options(list) {
    this._options = Array.isArray(list) ? list : [];
    this._render();
  }

  get options() {
    return this._options;
  }

  get value() {
    return this._inputEl?.value || '';
  }

  set value(val) {
    if (this._inputEl) {
      this._inputEl.value = val || '';
    }
  }

  get selectedId() {
    return this._selected?.id || null;
  }

  get selectedOption() {
    return this._selected;
  }

  clear() {
    this._selected = null;
    this.value = '';
    this._render();
    this.dispatchEvent(new Event('change', { bubbles: true }));
  }

  open() {
    this._listEl?.classList.remove('hidden');
    this._render(this.value);
  }

  close() {
    this._listEl?.classList.add('hidden');
  }

  selectById(optionId) {
    const match = this._options.find((opt) => opt.id === optionId);
    if (match) {
      this._select(match, false);
    }
  }

  _filter() {
    this._render(this.value);
    this.open();
  }

  _select(option, fireEvent) {
    this._selected = option;
    this.value = option.text;
    this.close();

    if (fireEvent) {
      this.dispatchEvent(
        new CustomEvent('select', {
          bubbles: true,
          detail: option,
        })
      );
      this.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }

  _handleDocumentClick(event) {
    if (!this.contains(event.target)) {
      this.close();
    }
  }

  _build() {
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

    this._labelEl = this.querySelector('[data-part="label"]');
    this._inputEl = this.querySelector('[data-part="input"]');
    this._listEl = this.querySelector('[data-part="list"]');

    if (this.hasAttribute('value')) {
      this.value = this.getAttribute('value') || '';
    }

    this._inputEl.addEventListener('input', () => this._filter());
    this._inputEl.addEventListener('focus', () => this.open());
    this._inputEl.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        this.close();
      }
    });
  }

  _renderEmptyState() {
    const empty = document.createElement('div');
    empty.className = 'px-3 py-2 text-sm text-gray-500 dark:text-gray-400';
    empty.textContent = this.getAttribute('empty-text') || 'No results';
    this._listEl.appendChild(empty);
  }

  _renderListItem(option) {
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

  _renderList(filtered) {
    this._listEl.innerHTML = '';

    if (!filtered.length) {
      this._renderEmptyState();
      return;
    }

    filtered.forEach((option) => this._renderListItem(option));
  }

  _render(filterValue = '') {
    if (!this._listEl) return;

    const normalized = filterValue.trim().toLowerCase();
    const filtered = normalized
      ? this._options.filter((opt) => opt.text.toLowerCase().includes(normalized))
      : this._options;

    this._renderList(filtered);
  }
}
customElements.define('at-dropdown', AtDropdown);
