import { ApplicationConfig, provideZoneChangeDetection, importProvidersFrom, InjectionToken } from '@angular/core';
import { APP_BASE_HREF } from '@angular/common';
import { provideRouter } from '@angular/router';
import { routes } from './app.routes';
import { provideHttpClient, withFetch, withInterceptors } from '@angular/common/http';
import { provideTranslateHttpLoader } from '@ngx-translate/http-loader';
import { JwtInterceptor } from './interceptors/jwt.interceptor';
import { environment } from 'environments/environment';
import { provideMomentDateAdapter } from "@angular/material-moment-adapter";
import { provideHighlightOptions } from 'ngx-highlightjs';

export const REST_API_URL = new InjectionToken<string>('REST_API_URL');
export const API_DATA_FORMAT = new InjectionToken<string>('API_DATA_FORMAT');

import { MAT_FORM_FIELD_DEFAULT_OPTIONS } from '@angular/material/form-field';
import { provideTranslateService } from "@ngx-translate/core";

const getInitialLang = (): string => {
  if (typeof window === 'undefined') {
    return 'en_US';
  }
  try {
    const rawLang = localStorage.getItem('lang');
    if (rawLang) {
      try {
        const parsed = JSON.parse(rawLang);
        if (parsed) {
          const clean = String(parsed).replace(/['"]+/g, '').trim();
          if (clean) return clean;
        }
      } catch {
        const clean = rawLang.replace(/['"]+/g, '').trim();
        if (clean) return clean;
      }
    }
    const rawUiConfig = localStorage.getItem('ui_config');
    if (rawUiConfig) {
      const parsedConfig = JSON.parse(rawUiConfig);
      const loc = parsedConfig?.locale;
      if (loc) {
        if (typeof loc === 'object') {
          const key = loc.key || loc.id;
          if (key) return String(key).replace(/['"]+/g, '').trim();
        }
        return String(loc).replace(/['"]+/g, '').trim();
      }
    }
  } catch {
    // fallback
  }
  return 'en_US';
};

export const appConfig: ApplicationConfig = {
  providers: [
    { provide: MAT_FORM_FIELD_DEFAULT_OPTIONS, useValue: { appearance: 'outline' } },
    provideHighlightOptions({
      coreLibraryLoader: () => import('highlight.js/lib/core'),
      lineNumbersLoader: () => import('ngx-highlightjs/line-numbers'), // Optional, add line numbers if needed
      languages: {
        json: () => import('highlight.js/lib/languages/json')
      }
    }),
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideMomentDateAdapter(undefined, { useUtc: true }),
    { provide: REST_API_URL, useValue: environment.apiUrl },
    { provide: API_DATA_FORMAT, useValue: environment.apiDateFormat },
    { provide: APP_BASE_HREF, useValue: environment.appContext },

    provideRouter(routes),
    provideHttpClient(
      withFetch(), withInterceptors([JwtInterceptor])
    ),
    provideTranslateService({
      loader: provideTranslateHttpLoader({
        prefix: './assets/i18n/',
        suffix: '.json'
      }),
      fallbackLang: 'en_US',
      lang: getInitialLang()
    })
  ]
};