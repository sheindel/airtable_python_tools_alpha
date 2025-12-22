const template = document.createElement('template');

template.innerHTML = `
  <style>
    :host {
      display: block;
      font-family: inherit;
      position: relative;
    }

    .label {
      display: block;
      margin-bottom: 6px;
      font-size: 0.9rem;
      color: rgb(75, 85, 99);
    }

    .wrapper {
      position: relative;
    }

    input {
      width: 100%;
      box-sizing: border-box;
      padding: 10px 12px;
      border: 1px solid rgb(209, 213, 219);
      border-radius: 8px;
      background: var(--at-dropdown-bg, white);
      color: var(--at-dropdown-color, rgb(17, 24, 39));
      outline: none;
      transition: border-color 120ms ease, box-shadow 120ms ease;
    }

    input:focus {
      border-color: rgb(59, 130, 246);
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
    }

    input[disabled] {
      background: rgb(243, 244, 246);
      cursor: not-allowed;
    }

    .list {
      position: absolute;
      top: calc(100% + 4px);
      left: 0;
      right: 0;
      max-height: 240px;
      overflow-y: auto;
      background: var(--at-dropdown-bg, white);
      border: 1px solid rgb(209, 213, 219);
      border-radius: 8px;
      box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
      z-index: 10;
      padding: 4px 0;
    }

    .list.hidden {
      display: none;
    }

    .item {
      padding: 8px 12px;
      cursor: pointer;
      color: var(--at-dropdown-color, rgb(17, 24, 39));
    }

    .item:hover,
    .item[aria-selected="true"] {
      background: rgba(59, 130, 246, 0.12);
      color: rgb(37, 99, 235);
    }

    .empty {
      padding: 10px 12px;
      color: rgb(107, 114, 128);
      font-size: 0.9rem;
    }
  </style>
  <label class="label"></label>
  <div class="wrapper">
    <input part="input" type="text" autocomplete="off" />
    <div class="list hidden" part="list"></div>
  </div>
`;

export class AtDropdown extends HTMLElement {
  constructor() {
    super();
    this._options = [];
    this._selected = null;
    this._onDocumentClick = this._handleDocumentClick.bind(this);
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.appendChild(template.content.cloneNode(true));
  }

  connectedCallback() {
    this._labelEl = this.shadowRoot.querySelector('.label');
    this._inputEl = this.shadowRoot.querySelector('input');
    this._listEl = this.shadowRoot.querySelector('.list');

    this._inputEl.placeholder = this.getAttribute('placeholder') || '';
    this._labelEl.textContent = this.getAttribute('label') || '';

    if (this.hasAttribute('value')) {
      this.value = this.getAttribute('value') || '';
    }

    if (this.hasAttribute('disabled')) {
      this._inputEl.setAttribute('disabled', '');
    }

    this._inputEl.addEventListener('input', () => this._filter());
    this._inputEl.addEventListener('focus', () => this.open());
    this._inputEl.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        this.close();
      }
    });

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

  _render(filterValue = '') {
    if (!this._listEl) return;

    const normalized = filterValue.trim().toLowerCase();
    const filtered = normalized
      ? this._options.filter((opt) => opt.text.toLowerCase().includes(normalized))
      : this._options;

    this._listEl.innerHTML = '';

    if (!filtered.length) {
      const empty = document.createElement('div');
      empty.className = 'empty';
      empty.textContent = this.getAttribute('empty-text') || 'No results';
      this._listEl.appendChild(empty);
      return;
    }

    filtered.forEach((option) => {
      const item = document.createElement('div');
      item.className = 'item';
      item.textContent = option.text;
      item.setAttribute('role', 'option');
      if (this._selected && this._selected.id === option.id) {
        item.setAttribute('aria-selected', 'true');
      }
      item.addEventListener('click', () => this._select(option, true));
      this._listEl.appendChild(item);
    });
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
    if (!this.contains(event.target) && !this.shadowRoot.contains(event.target)) {
      this.close();
    }
  }
}

customElements.define('at-dropdown', AtDropdown);
