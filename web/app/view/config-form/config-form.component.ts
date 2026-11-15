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

export interface AuditLogPartOption {
    code: string;
    nameKey: string;
    descKey: string;
}

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
    isSubmitting = false;
    hideIndexPassword = true;
    hideDashboardPassword = true;
    hideIpxaKey = true;

    readonly auditLogPartOptions: AuditLogPartOption[] = [
        { code: 'A', nameKey: 'CONFIG_PAGE.AUDIT_PART_A_NAME', descKey: 'CONFIG_PAGE.AUDIT_PART_A_DESC' },
        { code: 'B', nameKey: 'CONFIG_PAGE.AUDIT_PART_B_NAME', descKey: 'CONFIG_PAGE.AUDIT_PART_B_DESC' },
        { code: 'C', nameKey: 'CONFIG_PAGE.AUDIT_PART_C_NAME', descKey: 'CONFIG_PAGE.AUDIT_PART_C_DESC' },
        { code: 'E', nameKey: 'CONFIG_PAGE.AUDIT_PART_E_NAME', descKey: 'CONFIG_PAGE.AUDIT_PART_E_DESC' },
        { code: 'F', nameKey: 'CONFIG_PAGE.AUDIT_PART_F_NAME', descKey: 'CONFIG_PAGE.AUDIT_PART_F_DESC' },
        { code: 'H', nameKey: 'CONFIG_PAGE.AUDIT_PART_H_NAME', descKey: 'CONFIG_PAGE.AUDIT_PART_H_DESC' },
        { code: 'I', nameKey: 'CONFIG_PAGE.AUDIT_PART_I_NAME', descKey: 'CONFIG_PAGE.AUDIT_PART_I_DESC' },
        { code: 'J', nameKey: 'CONFIG_PAGE.AUDIT_PART_J_NAME', descKey: 'CONFIG_PAGE.AUDIT_PART_J_DESC' },
        { code: 'K', nameKey: 'CONFIG_PAGE.AUDIT_PART_K_NAME', descKey: 'CONFIG_PAGE.AUDIT_PART_K_DESC' },
        { code: 'Z', nameKey: 'CONFIG_PAGE.AUDIT_PART_Z_NAME', descKey: 'CONFIG_PAGE.AUDIT_PART_Z_DESC' },
    ];
    readonly canonicalOrder = ['A', 'B', 'C', 'E', 'F', 'H', 'I', 'J', 'K', 'Z'];

    auditLogPartsControl = new FormControl<string[]>(['A', 'B', 'H', 'F']);

    form = new FormGroup({
        _id: new FormControl<string>(''),
        ca_certificate: new FormControl<string>(''),
        ca_private: new FormControl<string>(''),
        acme_directory_url: new FormControl<string>(''),
        dns_resolver: new FormControl<string>(''),
        logging: new FormGroup({
            mode: new FormControl<string>('local'),
            audit_log_parts: new FormControl<string>('ABHF'),
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
        this.auditLogPartsControl.valueChanges.subscribe(parts => {
            if (parts) {
                const sorted = [...parts].sort((a, b) => {
                    const idxA = this.canonicalOrder.indexOf(a);
                    const idxB = this.canonicalOrder.indexOf(b);
                    return (idxA === -1 ? 99 : idxA) - (idxB === -1 ? 99 : idxB);
                }).join('');
                if (this.form.get('logging.audit_log_parts')?.value !== sorted) {
                    this.form.get('logging.audit_log_parts')?.setValue(sorted);
                    this.form.markAsDirty();
                }
            }
        });

        // Fetch active configuration and patch form values
        this.configService.getActive().subscribe(data => {
            const c = (data as any)?.config || data;
            const rawParts = c.logging?.audit_log_parts || 'ABHF';
            const partsArray = rawParts.toUpperCase().split('').filter((ch: string) => this.canonicalOrder.includes(ch));
            this.auditLogPartsControl.setValue(partsArray, { emitEvent: false });

            this.form.patchValue({
                _id: c._id,
                ca_certificate: c.ca_certificate,
                ca_private: c.ca_private,
                acme_directory_url: c.acme_directory_url,
                dns_resolver: c.dns_resolver,
                logging: c.logging ? {
                    mode: c.logging.mode || 'local',
                    audit_log_parts: c.logging.audit_log_parts || 'ABHF',
                    type: c.logging.type || 'elasticsearch',
                    index_url: c.logging.index_url ?? c.logging.url ?? '',
                    index_username: c.logging.index_username ?? c.logging.username ?? '',
                    index_password: c.logging.index_password ?? c.logging.password ?? '',
                    dashboard_url: c.logging.dashboard_url ?? '',
                    dashboard_username: c.logging.dashboard_username ?? '',
                    dashboard_password: c.logging.dashboard_password ?? ''
                } : {
                    mode: 'local',
                    audit_log_parts: 'ABHF',
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

        this.isSubmitting = true;
        const formData = this.form.value as Config;
        this.configService.update(formData._id, formData).subscribe({
            next: () => {
                this.isSubmitting = false;
                this.notificationService.openSnackBar(this.translate.instant('CONFIG_PAGE.SUCCESS_SAVE'));
            },
            error: (err) => {
                this.isSubmitting = false;
                this.notificationService.openSnackBar(this.translate.instant('CONFIG_PAGE.ERROR_SAVE') + (err?.message ? ': ' + err.message : ''));
            }
        });
    }

    setAuditLogPreset(preset: string): void {
        const parts = preset.split('').filter((ch: string) => this.canonicalOrder.includes(ch));
        this.auditLogPartsControl.setValue(parts);
        this.form.get('logging.audit_log_parts')?.setValue(preset);
        this.form.markAsDirty();
    }

    isAuditPresetActive(preset: string): boolean {
        return this.form.get('logging.audit_log_parts')?.value === preset;
    }

    onAuditLogPartsInput(event: Event): void {
        const input = event.target as HTMLInputElement;
        if (input && input.value) {
            const upper = input.value.toUpperCase();
            if (input.value !== upper) {
                input.value = upper;
                this.form.get('logging.audit_log_parts')?.setValue(upper, { emitEvent: false });
            }
        }
    }

    get f(): { [key: string]: AbstractControl } {
        return this.form.controls;
    }
}