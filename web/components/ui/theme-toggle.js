const template = document.createElement('template');

template.innerHTML = `
  <style>
    :host {
      display: inline-flex;
    }
    button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 8px;
      border: none;
      border-radius: 10px;
      background: var(--at-toggle-bg, rgb(229, 231, 235));
      color: var(--at-toggle-color, rgb(55, 65, 81));
      cursor: pointer;
      transition: background 120ms ease, color 120ms ease, transform 120ms ease;
    }
    button:hover {
      background: rgb(209, 213, 219);
      transform: translateY(-1px);
    }
    svg {
      width: 18px;
      height: 18px;
    }
  </style>
  <button type="button" aria-label="Toggle dark mode">
    <span class="icon"></span>
  </button>
`;

const sunIcon = `
  <svg fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
    <path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" fill-rule="evenodd" clip-rule="evenodd"></path>
  </svg>
`;

const moonIcon = `
  <svg fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
    <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"></path>
  </svg>
`;

export class ThemeToggle extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.appendChild(template.content.cloneNode(true));
  }

  connectedCallback() {
    this._button = this.shadowRoot.querySelector('button');
    this._icon = this.shadowRoot.querySelector('.icon');
    this._button.addEventListener('click', () => this._toggle());
    this._applyInitialTheme();
  }

  disconnectedCallback() {
    this._button?.removeEventListener('click', this._toggle);
  }

  _applyInitialTheme() {
    const saved = localStorage.getItem('color-theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const useDark = saved === 'dark' || (!saved && prefersDark);
    document.documentElement.classList.toggle('dark', useDark);
    this._renderIcon(useDark);
  }

  _toggle() {
    const isDark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('color-theme', isDark ? 'dark' : 'light');
    this._renderIcon(isDark);
    this.dispatchEvent(new CustomEvent('theme-change', {
      bubbles: true,
      detail: { theme: isDark ? 'dark' : 'light' }
    }));
  }

  _renderIcon(isDark) {
    if (!this._icon) return;
    this._icon.innerHTML = isDark ? sunIcon : moonIcon;
  }
}

customElements.define('at-theme-toggle', ThemeToggle);
