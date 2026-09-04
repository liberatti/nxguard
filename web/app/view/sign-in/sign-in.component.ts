import {HttpClient} from '@angular/common/http';
import {Component, OnInit} from '@angular/core';
import {FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators} from '@angular/forms';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatOptionModule} from '@angular/material/core';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatGridListModule} from '@angular/material/grid-list';
import {MatIconModule} from '@angular/material/icon';
import {MatInputModule} from '@angular/material/input';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {MatSelectModule} from '@angular/material/select';
import {MatMenuModule} from '@angular/material/menu';
import {MatTooltipModule} from '@angular/material/tooltip';
import {Router, RouterModule} from '@angular/router';
import {User} from 'app/models/oauth';
import {Language} from 'app/models/shared';
import {LocalStorageService} from 'app/services/localstorage.service';
import {NotificationService} from 'app/services/notification.service';
import {OAuthService} from 'app/services/oauth.service';
import {CommonModule} from "@angular/common";
import {TranslatePipe, TranslateService} from "@ngx-translate/core";
import {environment} from "environments/environment";

@Component({
    selector: 'app-sign-in',
    standalone: true,
    imports: [RouterModule, CommonModule, FormsModule, ReactiveFormsModule, TranslatePipe,
        MatIconModule, MatButtonModule, MatFormFieldModule,
        MatCardModule, MatProgressBarModule, MatInputModule,
        MatTooltipModule, MatSelectModule, MatOptionModule, MatGridListModule, MatMenuModule
    ],

    templateUrl: './sign-in.component.html',
    styleUrl: './sign-in.component.css'
})
export class SignInComponent implements OnInit {
    locales = [] as Array<Language>;
    hidePassword = true;
    isDarkMode = false;
    version: string = environment.version;
    currentYear: number = new Date().getFullYear();
    currentLangCode: string = 'EN';

    form = new FormGroup({
        email: new FormControl<string>('', {
            validators: [
                Validators.required,
            ],
        }),
        password: new FormControl<string>('', {
            validators: [
                Validators.required,
            ],
        }),
        locale: new FormControl<string>('en_US'),
    });

    constructor(private router: Router,
                private auth: OAuthService, private http: HttpClient,
                private localStorage: LocalStorageService,
                private notificationService: NotificationService,
                private translate: TranslateService) {
    }

    ngOnInit() {
        this.logout();
        this.locales = [
            { id: 'en_US', name: 'English (US)' },
            { id: 'pt_BR', name: 'Português (BR)' }
        ];
        const uiConfig = this.localStorage.get('ui_config');
        const uiLocale = uiConfig?.locale ? (typeof uiConfig.locale === 'object' ? (uiConfig.locale.key || uiConfig.locale.id) : uiConfig.locale) : null;
        const savedLang = this.localStorage.get('lang') || uiLocale || 'en_US';
        this.translate.use(savedLang);
        this.form.controls.locale.setValue(savedLang);
        this.updateLangCode(savedLang);

        const savedTheme = this.localStorage.get('theme');
        if (savedTheme === 'dark') {
            this.isDarkMode = true;
            document.documentElement.setAttribute('data-theme', 'dark');
            document.body.classList.add('dark-theme');
        }
    }

    updateLangCode(lang: string) {
        this.currentLangCode = lang && lang.toLowerCase().startsWith('pt') ? 'PT' : 'EN';
    }

    toggleTheme() {
        this.isDarkMode = !this.isDarkMode;
        if (this.isDarkMode) {
            document.documentElement.setAttribute('data-theme', 'dark');
            document.body.classList.add('dark-theme');
            this.localStorage.set('theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
            document.body.classList.remove('dark-theme');
            this.localStorage.set('theme', 'light');
        }
    }

    onLocaleChange(lang: string) {
        const selectedLang = lang || 'en_US';
        this.translate.use(selectedLang);
        this.localStorage.set('lang', selectedLang);

        let uiConfig = this.localStorage.get('ui_config');
        if (!uiConfig) {
            uiConfig = {
                locale: selectedLang,
                sidenavOpened: true,
                navResource: 'dashboard',
                display: { datetime: 'YYYY-MM-DDTHH:mm:ss' }
            };
        } else {
            uiConfig.locale = selectedLang;
        }
        this.localStorage.set('ui_config', uiConfig);
        this.form.controls.locale.setValue(selectedLang);
        this.updateLangCode(selectedLang);
    }

    login() {
        if (this.form.status === "INVALID") {
            return;
        }
        const formData = this.form.value as User;
        this.auth.login(formData).subscribe({
            next: (data) => {
                this.auth.storeTokens(data);
                this.router.navigate(['/dashboard']).then(r => true);
            },
            error: (err) => {
                this.notificationService.openSnackBar("Authentication failed");
                this.router.navigate(['/signin']).then(r => true);
            }
        });
    }

    logout() {
        this.auth.logout();
        this.localStorage.remove('oidc');
    }
}

