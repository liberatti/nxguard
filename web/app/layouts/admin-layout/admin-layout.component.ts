import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { AfterViewInit, ChangeDetectorRef, Component, Injector, NgZone, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule } from '@angular/material/menu';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { ActivatedRoute, NavigationEnd, Router, RouterModule } from '@angular/router';
import { TranslatePipe, TranslateService } from '@ngx-translate/core';
import * as moment from 'moment';
import { filter, Subject, takeUntil } from 'rxjs';
import { FrontendConfig, MenuLink } from 'app/models/shared';
import { LocalStorageService } from 'app/services/localstorage.service';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { AboutDialogComponent } from 'app/components/about-dialog/about-dialog.component';
import { ApplyDialogComponent } from 'app/components/apply-dialog/apply-dialog.component';
import { MatBadgeModule } from '@angular/material/badge';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { OAuthService } from 'app/services/oauth.service';
import { io } from 'socket.io-client';
import { REST_API_URL } from 'app/app.config';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { HttpClient } from '@angular/common/http';
import { environment } from 'environments/environment';
import { ConfigService, HealthService } from '../../services/config.service';
import { Health } from '../../models/config';
import { ThemeService } from 'app/services/theme.service';

import mainMenuData from '../../../assets/main.menu.json';

@Component({
    selector: 'app-admin-layout',
    standalone: true,
    imports: [
        RouterModule,
        CommonModule,
        TranslatePipe,
        MatProgressBarModule,
        MatSidenavModule,
        MatIconModule,
        MatToolbarModule,
        MatCardModule,
        MatChipsModule,
        MatButtonModule,
        MatListModule,
        MatMenuModule,
        MatBadgeModule,
        MatTooltipModule
    ],
    templateUrl: './admin-layout.component.html',
    styleUrl: './admin-layout.component.css'
})
export class AdminLayoutComponent implements OnInit, AfterViewInit, OnDestroy {

    title: string = environment.name;
    version: string = environment.version;
    config: FrontendConfig = <FrontendConfig>{ locale: { key: 'en_US' }, navResource: 'transaction', sidenavOpened: false };
    destroyed = new Subject<void>();
    currentScreenSize: string = '';
    updatePending: boolean = false;
    health: Health = {} as Health;

    displayNameMap = new Map([
        [Breakpoints.XSmall, 'XSmall'],
        [Breakpoints.Small, 'Small'],
        [Breakpoints.Medium, 'Medium'],
        [Breakpoints.Large, 'Large'],
        [Breakpoints.XLarge, 'XLarge'],
    ]);
    protected httpClient: HttpClient;
    menu: Array<MenuLink> = (mainMenuData as unknown) as Array<MenuLink>;
    changes: Array<any> = [];
    socket: any;
    trackingEvt: boolean = false;
    applyDialogRef: MatDialogRef<ApplyDialogComponent> | null = null;

    constructor(
        private changeDetectorRef: ChangeDetectorRef,
        protected oauth: OAuthService,
        private localStorage: LocalStorageService,
        private breakpointObserver: BreakpointObserver,
        private translate: TranslateService,
        private portDialog: MatDialog,
        private applyDialog: MatDialog,
        private configService: ConfigService,
        protected injector: Injector,
        private route: ActivatedRoute,
        private router: Router,
        private healthService: HealthService,
        private ngZone: NgZone,
        public themeService: ThemeService
    ) {
        this.httpClient = this.injector.get(HttpClient);
        breakpointObserver
            .observe([
                Breakpoints.XSmall,
                Breakpoints.Small,
                Breakpoints.Medium,
                Breakpoints.Large,
                Breakpoints.XLarge,
            ])
            .pipe(takeUntil(this.destroyed))
            .subscribe(result => {
                for (const query of Object.keys(result.breakpoints)) {
                    if (result.breakpoints[query]) {
                        this.currentScreenSize = this.displayNameMap.get(query) ?? 'Unknown';
                    }
                }
            });
        this.config = this.localStorage.get('ui_config');
    }

    signOut() {
        this.oauth.resetTokens();
        this.router.navigate(['/signin']);
    }

    isMobile() {
        return ['XSmall', 'Small'].includes(this.currentScreenSize);
    }

    isSidenavActive() {
        return this.config && this.config.sidenavOpened;
    }

    onMenuClick() {
        if (this.isMobile() && this.config) {
            this.config.sidenavOpened = false;
        }
    }

    toggleSubMenu(link: MenuLink | undefined) {
        if (!link) {
            const currentRoute = this.router.url;
            for (const m of this.menu) {
                if (m.menu && Array.isArray(m.menu)) {
                    for (const sm of m.menu) {
                        if (sm.route && currentRoute.includes(sm.route)) {
                            m.expanded = true;
                            break;
                        }
                    }
                }
            }
        } else {
            link.expanded = !link.expanded;
        }
    }

    onSidenavToggle() {
        window.dispatchEvent(new Event('resize'));
        if (this.config) {
            this.config.sidenavOpened = !this.config.sidenavOpened;
            this.localStorage.set('ui_config', this.config);
        }
    }

    healthCheck() {
        this.healthService.check().subscribe(data => {
            this.health = data;
            if (data && data.apply_pendding) {
                this.changes = data.apply_pendding;
                this.trackingEvt = this.changes.length > 0;
                this.changeDetectorRef.detectChanges();
            }
        });
    }

    loadChanges() {
        this.configService.getChanges().subscribe({
            next: (res) => {
                const data = res && res.data ? res.data : (Array.isArray(res) ? res : []);
                this.changes = data;
                this.trackingEvt = this.changes.length > 0;
                this.changeDetectorRef.detectChanges();
            },
            error: () => {
                this.healthCheck();
            }
        });
    }

    ngOnInit(): void {
        this.translate.setFallbackLang('en_US');
        const savedLang = this.localStorage.get('lang');
        if (savedLang) {
            this.translate.use(savedLang);
            moment.locale(savedLang);
        }
        this.menu = (mainMenuData as unknown) as Array<MenuLink>;
        this.toggleSubMenu(undefined);
        this.httpClient.get<any>('assets/main.menu.json').subscribe({
            next: (data) => {
                if (data && data.length > 0) {
                    this.menu = data;
                }
                this.toggleSubMenu(undefined);
            },
            error: () => {
                this.toggleSubMenu(undefined);
            }
        });
        this.router.events
            .pipe(
                filter((event) => event instanceof NavigationEnd),
                takeUntil(this.destroyed)
            )
            .subscribe(() => {
                this.loadChanges();
            });
        this.loadChanges();
    }

    showAbout() {
        this.portDialog.open(AboutDialogComponent, {
            width: '560px',
            maxWidth: '95vw'
        });
    }

    onApply() {
        this.applyDialogRef = this.applyDialog.open(ApplyDialogComponent, {
            width: '480px',
            disableClose: false,
            data: { changes: this.changes }
        });
        this.applyDialogRef.afterClosed().subscribe((applied) => {
            this.loadChanges();
        });
    }

    ngAfterViewInit(): void {
        const savedLang = this.localStorage.get('lang');
        if (this.localStorage.exists('ui_config')) {
            this.config = this.localStorage.get('ui_config');
            if (savedLang && this.config) {
                this.config.locale = savedLang;
                this.localStorage.set('ui_config', this.config);
            }
        } else {
            this.config = {
                locale: savedLang || 'en_US',
                navResource: 'dashboard',
                sidenavOpened: true,
                display: {
                    datetime: 'YYYY-MM-DDTHH:mm:ss'
                }
            } as FrontendConfig;
            this.localStorage.set('ui_config', this.config);
        }
        const langKey = savedLang || (typeof this.config.locale === 'object' ? (this.config.locale?.key || this.config.locale?.id || 'en_US') : (this.config.locale || 'en_US'));
        this.translate.use(langKey);
        moment.locale(langKey);

        this.changeDetectorRef.detectChanges();
        const apiUrl = this.injector.get(REST_API_URL);
        if (!apiUrl) {
            console.error('REST_API_URL not found in injector');
            return;
        }
        const url = new URL(apiUrl);
        this.socket = io(url.origin, {
            path: `${url.pathname}/socket.io`.replace('//', '/'),
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 10000,
            reconnectionDelayMax: 20000,
            timeout: 10000,
        });

        this.socket.on('tracking_evt', () => {
            this.ngZone.run(() => {
                this.loadChanges();
            });
        });

        this.socket.on('tracking_aply', () => {
            this.ngZone.run(() => {
                this.trackingEvt = false;
                this.changes = [];
                this.changeDetectorRef.detectChanges();
            });
        });

    }

    ngOnDestroy() {
        this.destroyed.next();
        this.destroyed.complete();
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}