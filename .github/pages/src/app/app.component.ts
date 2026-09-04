import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatTabsModule } from '@angular/material/tabs';
import { MatDividerModule } from '@angular/material/divider';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatMenuModule } from '@angular/material/menu';
import { TranslatePipe, TranslateDirective, TranslateService } from '@ngx-translate/core';
import packageJson from '../../package.json';

interface FeatureItem {
  icon: string;
  titleKey: string;
  badgeKey: string;
  descriptionKey: string;
}

interface ScreenshotItem {
  id: string;
  titleKey: string;
  subtitleKey: string;
  image: string;
  descriptionKey: string;
}

interface MetricItem {
  labelKey: string;
  valueKey: string;
  captionKey: string;
}

interface LanguageOption {
  code: string;
  labelKey: string;
  flag: string;
  short: string;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    MatToolbarModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatChipsModule,
    MatTabsModule,
    MatDividerModule,
    MatTooltipModule,
    MatMenuModule,
    TranslatePipe,
    TranslateDirective
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  private readonly translate = inject(TranslateService);

  readonly title = 'NXGuard';
  readonly version = `${packageJson.version}`;

  readonly supportedLanguages: LanguageOption[] = [
    { code: 'en_US', labelKey: 'PAGES.NAV.LANG_EN', flag: '🇺🇸', short: 'EN' },
    { code: 'pt_BR', labelKey: 'PAGES.NAV.LANG_PT', flag: '🇧🇷', short: 'PT' }
  ];

  get currentLang(): string {
    return this.translate.currentLang() || (typeof window !== 'undefined' && localStorage.getItem('lang')) || 'en_US';
  }

  get currentLanguageOption(): LanguageOption {
    return this.supportedLanguages.find(l => l.code === this.currentLang) || this.supportedLanguages[0];
  }

  switchLanguage(langCode: string): void {
    this.translate.use(langCode);
    if (typeof window !== 'undefined') {
      localStorage.setItem('lang', langCode);
    }
  }

  readonly metrics: MetricItem[] = [
    {
      labelKey: 'PAGES.METRICS.LATENCY.LABEL',
      valueKey: 'PAGES.METRICS.LATENCY.VALUE',
      captionKey: 'PAGES.METRICS.LATENCY.CAPTION'
    },
    {
      labelKey: 'PAGES.METRICS.CRS.LABEL',
      valueKey: 'PAGES.METRICS.CRS.VALUE',
      captionKey: 'PAGES.METRICS.CRS.CAPTION'
    },
    {
      labelKey: 'PAGES.METRICS.ENGINE.LABEL',
      valueKey: 'PAGES.METRICS.ENGINE.VALUE',
      captionKey: 'PAGES.METRICS.ENGINE.CAPTION'
    },
    {
      labelKey: 'PAGES.METRICS.ANALYTICS.LABEL',
      valueKey: 'PAGES.METRICS.ANALYTICS.VALUE',
      captionKey: 'PAGES.METRICS.ANALYTICS.CAPTION'
    }
  ];

  readonly features: FeatureItem[] = [
    {
      icon: 'shield',
      titleKey: 'PAGES.FEATURES.MODSECURITY.TITLE',
      badgeKey: 'PAGES.FEATURES.MODSECURITY.BADGE',
      descriptionKey: 'PAGES.FEATURES.MODSECURITY.DESCRIPTION'
    },
    {
      icon: 'bolt',
      titleKey: 'PAGES.FEATURES.LUAJIT.TITLE',
      badgeKey: 'PAGES.FEATURES.LUAJIT.BADGE',
      descriptionKey: 'PAGES.FEATURES.LUAJIT.DESCRIPTION'
    },
    {
      icon: 'hub',
      titleKey: 'PAGES.FEATURES.IPXA.TITLE',
      badgeKey: 'PAGES.FEATURES.IPXA.BADGE',
      descriptionKey: 'PAGES.FEATURES.IPXA.DESCRIPTION'
    },
    {
      icon: 'analytics',
      titleKey: 'PAGES.FEATURES.DUCKDB.TITLE',
      badgeKey: 'PAGES.FEATURES.DUCKDB.BADGE',
      descriptionKey: 'PAGES.FEATURES.DUCKDB.DESCRIPTION'
    },
    {
      icon: 'vpn_key',
      titleKey: 'PAGES.FEATURES.ACME.TITLE',
      badgeKey: 'PAGES.FEATURES.ACME.BADGE',
      descriptionKey: 'PAGES.FEATURES.ACME.DESCRIPTION'
    },
    {
      icon: 'alt_route',
      titleKey: 'PAGES.FEATURES.ROUTING.TITLE',
      badgeKey: 'PAGES.FEATURES.ROUTING.BADGE',
      descriptionKey: 'PAGES.FEATURES.ROUTING.DESCRIPTION'
    }
  ];

  readonly screenshots: ScreenshotItem[] = [
    {
      id: 'dashboard',
      titleKey: 'PAGES.SCREENSHOTS.DASHBOARD.TITLE',
      subtitleKey: 'PAGES.SCREENSHOTS.DASHBOARD.SUBTITLE',
      image: 'assets/dashboard.png',
      descriptionKey: 'PAGES.SCREENSHOTS.DASHBOARD.DESCRIPTION'
    },
    {
      id: 'transactions',
      titleKey: 'PAGES.SCREENSHOTS.TRANSACTIONS.TITLE',
      subtitleKey: 'PAGES.SCREENSHOTS.TRANSACTIONS.SUBTITLE',
      image: 'assets/transactions.png',
      descriptionKey: 'PAGES.SCREENSHOTS.TRANSACTIONS.DESCRIPTION'
    },
    {
      id: 'raw-inspection',
      titleKey: 'PAGES.SCREENSHOTS.RAW_INSPECTION.TITLE',
      subtitleKey: 'PAGES.SCREENSHOTS.RAW_INSPECTION.SUBTITLE',
      image: 'assets/transaction-raw.png',
      descriptionKey: 'PAGES.SCREENSHOTS.RAW_INSPECTION.DESCRIPTION'
    },
    {
      id: 'rule-details',
      titleKey: 'PAGES.SCREENSHOTS.RULE_DETAILS.TITLE',
      subtitleKey: 'PAGES.SCREENSHOTS.RULE_DETAILS.SUBTITLE',
      image: 'assets/transaction-rule-raw.png',
      descriptionKey: 'PAGES.SCREENSHOTS.RULE_DETAILS.DESCRIPTION'
    }
  ];

  readonly composeCode = `services:
  main:
    image: liberatti/nxguard:latest
    environment:
      NXGUARD_ROLE: "main"
      SERVERID: "nxguard-main"
    ports:
      - "8000:5000"     # Management Dashboard
      - "8001:80"       # HTTP Ingress
      - "8443:443"      # HTTPS Ingress
    deploy:
      resources:
        limits:
          memory: 256M
    restart: unless-stopped
    volumes:
      - nxguard_data:/data
    extra_hosts:
      - "host.docker.internal:host-gateway"

  ipxa:
    image: liberatti/ipxa:latest
    environment:
      - API_KEY=xxxxxxxx
      - IPINFO_TOKEN=xxxxxxxx
      - LOGLEVEL=INFO
      - SECURITY_ENABLED=true
      - IBLOCKLIST_USERNAME=xxxxxxxx
      - IBLOCKLIST_PASSWORD=xxxxxxxx
      - MAXMIND_ACCOUNT_ID=xxxxxxxx
      - MAXMIND_LICENSE_KEY=xxxxxxxx
    volumes:
      - ipxa_data:/opt/ipxa/data
    deploy:
      resources:
        limits:
          memory: 128M
    restart: unless-stopped

volumes:
  ipxa_data:
  nxguard_data:`;

  readonly gotestwafCode = `docker run --rm \\
  --shm-size=2g \\
  --add-host nxguard.local:host-gateway \\
  -v \${PWD}/.github/pages/src/assets/reports:/app/reports \\
  wallarm/gotestwaf --url=http://nxguard.local:8080/nxg/ \\
  --blockStatusCodes=403,404,400 --reportFormat=html --noEmailReport`;

  copiedCompose = false;
  copiedGotestwaf = false;

  copyCompose(): void {
    navigator.clipboard.writeText(this.composeCode).then(() => {
      this.copiedCompose = true;
      setTimeout(() => (this.copiedCompose = false), 2000);
    });
  }

  copyGotestwaf(): void {
    navigator.clipboard.writeText(this.gotestwafCode).then(() => {
      this.copiedGotestwaf = true;
      setTimeout(() => (this.copiedGotestwaf = false), 2000);
    });
  }
}
