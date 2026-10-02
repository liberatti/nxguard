import { Component, OnInit } from '@angular/core';
import { Router, RouterModule } from '@angular/router';
import { AbstractControl, FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { ConfigService } from 'app/services/config.service';
import { NotificationService } from 'app/services/notification.service';
import { CommonModule } from '@angular/common';
import { MatMomentDateModule } from '@angular/material-moment-adapter';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule } from '@angular/material/menu';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatSortModule } from '@angular/material/sort';
import { MatTooltipModule } from '@angular/material/tooltip';
import { TranslatePipe, TranslateService } from '@ngx-translate/core';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { Config } from 'app/models/config';
import { MatTabsModule } from '@angular/material/tabs';
import { MatExpansionModule } from '@angular/material/expansion';
import { OAuthService } from "../../services/oauth.service";

import { TextFieldModule } from '@angular/cdk/text-field';

@Component({
    selector: 'app-config-form',
    standalone: true,
    imports: [
        RouterModule, CommonModule,
        ReactiveFormsModule, TranslatePipe,
        MatMomentDateModule,
        MatSidenavModule, MatIconModule, MatButtonModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule, MatSlideToggleModule,
        MatFormFieldModule, MatChipsModule, MatTabsModule, MatExpansionModule,
        TextFieldModule
    ],
    templateUrl: './config-form.component.html',
    styleUrl: './config-form.component.css'
})
export class ConfigFormComponent implements OnInit {
    submitted = false;
    form = new FormGroup({
        _id: new FormControl<string>(''),
        ca_certificate: new FormControl<string>(''),
        ca_private: new FormControl<string>(''),
        acme_directory_url: new FormControl<string>(''),
        dns_resolver: new FormControl<string>(''),
        logging: new FormGroup({
            mode: new FormControl<string>('local'),
            type: new FormControl<string>('elasticsearch'),
            index_url: new FormControl<string>(''),
            index_username: new FormControl<string>(''),
            index_password: new FormControl<string>(''),
            dashboard_url: new FormControl<string>(''),
            dashboard_username: new FormControl<string>(''),
            dashboard_password: new FormControl<string>(''),
        }),
        purge: new FormGroup({
            enabled: new FormControl<boolean>(false),
            purge_after: new FormControl<number>(1800)
        }),
        ipxa: new FormGroup({
            url: new FormControl<string>(''),
            key: new FormControl<string>('')
        }),
        telemetry: new FormGroup({
            enabled: new FormControl<boolean>(false),
            url: new FormControl<string>('')
        })
    });

    constructor(
        private notificationService: NotificationService,
        private router: Router,
        private configService: ConfigService,
        private translate: TranslateService,
        protected oauth: OAuthService,
    ) {
    }

    ngOnInit(): void {
        // Fetch active configuration and patch form values
        this.configService.getActive().subscribe(data => {
            const c = (data as any)?.config || data;
            this.form.patchValue({
                _id: c._id,
                ca_certificate: c.ca_certificate,
                ca_private: c.ca_private,
                acme_directory_url: c.acme_directory_url,
                dns_resolver: c.dns_resolver,
                logging: c.logging ? {
                    mode: c.logging.mode || 'local',
                    type: c.logging.type || 'elasticsearch',
                    index_url: c.logging.index_url ?? c.logging.url ?? '',
                    index_username: c.logging.index_username ?? c.logging.username ?? '',
                    index_password: c.logging.index_password ?? c.logging.password ?? '',
                    dashboard_url: c.logging.dashboard_url ?? '',
                    dashboard_username: c.logging.dashboard_username ?? '',
                    dashboard_password: c.logging.dashboard_password ?? ''
                } : {
                    mode: 'local',
                    type: 'elasticsearch',
                    index_url: '',
                    index_username: '',
                    index_password: '',
                    dashboard_url: '',
                    dashboard_username: '',
                    dashboard_password: ''
                },
                purge: c.purge || {},
                ipxa: c.ipxa || {}
            });
        });
    }

    onSubmit() {
        this.submitted = true;
        if (this.form.status === "INVALID") {
            let detailsObj: any = {};
            Object.keys(this.form.controls).forEach(k => {
                let control = this.form.get(k);
                if (control && control.status !== "VALID") {
                    detailsObj[k] = ["Invalid value on " + k];
                }
            });
            this.notificationService.openErrorSnackBar({
                code: 400,
                message: 'Validation Error',
                method: 'PUT',
                url: '/api/v1/config',
                details: detailsObj
            });
            return;
        }

        const formData = this.form.value as Config;
        this.configService.update(formData._id, formData).subscribe({
            next: () => {
                this.notificationService.openSnackBar(this.translate.instant('CONFIG_PAGE.SUCCESS_SAVE'));
            },
            error: (err) => {
                this.notificationService.openSnackBar(this.translate.instant('CONFIG_PAGE.ERROR_SAVE') + (err?.message ? ': ' + err.message : ''));
            }
        });
    }

    get f(): { [key: string]: AbstractControl } {
        return this.form.controls;
    }
}