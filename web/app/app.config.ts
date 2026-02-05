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

import { provideTranslateService, provideTranslateLoader } from "@ngx-translate/core";



export const appConfig: ApplicationConfig = {
  providers: [
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
        prefix: '/assets/i18n/',
        suffix: '.json'
      }),
      fallbackLang: 'en',
      lang: 'en'
    })
  ]
};