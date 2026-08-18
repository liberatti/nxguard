import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatTabsModule } from '@angular/material/tabs';
import { MatDividerModule } from '@angular/material/divider';
import { MatTooltipModule } from '@angular/material/tooltip';

interface FeatureItem {
  icon: string;
  title: string;
  badge: string;
  description: string;
}

interface ScreenshotItem {
  id: string;
  title: string;
  subtitle: string;
  image: string;
  description: string;
}

interface MetricItem {
  label: string;
  value: string;
  caption: string;
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
    MatTooltipModule
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  readonly title = 'NXGuard';
  readonly version = 'v1.0.8';

  readonly metrics: MetricItem[] = [
    { label: 'Latency Overhead', value: '< 0.4ms', caption: 'Sub-millisecond Layer 7 inspection' },
    { label: 'Core Rule Set', value: 'CRS 4.25+', caption: 'Latest OWASP threat rules' },
    { label: 'Engine Stack', value: 'Nginx + LuaJIT', caption: 'High concurrency OpenResty core' },
    { label: 'Analytics DB', value: 'DuckDB', caption: 'Embedded zero-overhead SQL telemetry' }
  ];

  readonly features: FeatureItem[] = [
    {
      icon: 'shield',
      title: 'Advanced ModSecurity v3 WAF',
      badge: 'Layer 7 Protection',
      description: 'Native integration with ModSecurity v3 and OWASP Core Rule Set 4.25+ protecting against SQLi, XSS, RCE, LFI/RFI, and zero-day vulnerabilities.'
    },
    {
      icon: 'bolt',
      title: 'High-Performance LuaJIT Core',
      badge: 'Sub-Millisecond',
      description: 'Custom Lua sensors running directly inside OpenResty worker threads for rapid request filtering, header sanitization, and rate-limiting.'
    },
    {
      icon: 'hub',
      title: 'IPXA Threat Intelligence',
      badge: 'Feed Sync',
      description: 'Continuous synchronization with IPXA for dynamic IP reputation, real-time threat feed integration, geo-blocking, and smart bypass rules.'
    },
    {
      icon: 'analytics',
      title: 'DuckDB Embedded Analytics',
      badge: 'Zero External DB',
      description: 'Columnar storage engine embedded directly in the admin backend for rapid real-time transaction query, aggregation, and auditing.'
    },
    {
      icon: 'vpn_key',
      title: 'ACME & SSL Automation',
      badge: 'Automated TLS',
      description: 'Automated certificate issuance and renewal via Let\'s Encrypt / ACME with HTTP-01 challenges and seamless Nginx reload.'
    },
    {
      icon: 'alt_route',
      title: 'Smart Reverse Proxy & Routing',
      badge: 'Traffic Control',
      description: 'Upstream health checks, session stickiness, HTTP method filtering, allowed content-type validation, and route-specific security policies.'
    }
  ];

  readonly screenshots: ScreenshotItem[] = [
    {
      id: 'dashboard',
      title: 'Executive Security Dashboard',
      subtitle: 'Real-time overview of threats, blocked requests, and system health',
      image: 'assets/dashboard.png',
      description: 'Intuitive management interface with live metrics, transaction counts, WAF alerts, and operational controls.'
    },
    {
      id: 'transactions',
      title: 'Transaction Stream & Monitoring',
      subtitle: 'Live transaction logging and traffic inspection',
      image: 'assets/transactions.png',
      description: 'Search, filter, and inspect incoming requests by service, status, IP, country, and threat score.'
    },
    {
      id: 'raw-inspection',
      title: 'Raw Request & Payload Inspection',
      subtitle: 'Deep dive into headers, query parameters, and body payloads',
      image: 'assets/transaction-raw.png',
      description: 'Complete inspection of raw HTTP transactions to investigate attacks and debug traffic anomalies.'
    },
    {
      id: 'rule-details',
      title: 'ModSecurity Rule Match Details',
      subtitle: 'Granular rule triggers and matched patterns',
      image: 'assets/transaction-rule-raw.png',
      description: 'Detailed analysis of matched ModSecurity rule IDs, tags, severity levels, and matched string segments.'
    }
  ];

  readonly composeCode = `services:
  nxguard:
    image: liberatti/nxguard:latest
    container_name: nxguard
    environment:
      NXGUARD_ROLE: "main"
      SERVERID: "nxguard-admin"
    ports:
      - "5000:5000" # Management Dashboard
      - "80:80"     # HTTP Ingress
      - "443:443"   # HTTPS Ingress
    deploy:
      resources:
        limits:
          memory: 256M
    restart: unless-stopped

  ipxa:
    image: liberatti/ipxa:latest
    container_name: ipxa
    volumes:
      - ipxa_data:/opt/ipxa/data
    deploy:
      resources:
        limits:
          memory: 64M
    restart: unless-stopped

volumes:
  ipxa_data:`;

  readonly gotestwafCode = `docker run --rm \\
  --shm-size=2g \\
  --add-host nxguard.local:host-gateway \\
  -v \${PWD}/.docs/reports:/app/reports \\
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
