// src/types/window.d.ts

import { Pinia } from 'pinia';

declare global {
  interface Window {
    Cypress?: any;
    pinia?: Pinia;
  }
}