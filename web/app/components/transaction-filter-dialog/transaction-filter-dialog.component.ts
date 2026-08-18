import { Component, Inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { TranslatePipe } from '@ngx-translate/core';

export interface FilterFieldOption {
    key: string;
    labelKey: string;
    category: 'GENERAL' | 'ROUTING' | 'NETWORK' | 'HTTP' | 'SECURITY' | 'SYSTEM';
    icon: string;
    type: 'enum' | 'text' | 'number' | 'boolean';
    options?: string[];
    presets?: any[];
    placeholder?: string;
}

@Component({
    selector: 'app-transaction-filter-dialog',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        ReactiveFormsModule,
        MatDialogModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatButtonModule,
        MatIconModule,
        MatChipsModule,
        MatTooltipModule,
        TranslatePipe,
    ],
    templateUrl: './transaction-filter-dialog.component.html',
    styleUrl: './transaction-filter-dialog.component.css',
})
export class TransactionFilterDialogComponent implements OnInit {
    filterForm!: FormGroup;

    readonly fields: FilterFieldOption[] = [
        // GENERAL
        {
            key: 'action',
            labelKey: 'TRANSACTION.FILTER.FIELDS.ACTION',
            category: 'GENERAL',
            icon: 'security',
            type: 'enum',
            options: ['DENY', 'ALLOW', 'WARN', 'REJECTED', 'PASSED'],
        },
        {
            key: 'score',
            labelKey: 'TRANSACTION.FILTER.FIELDS.SCORE',
            category: 'GENERAL',
            icon: 'speed',
            type: 'number',
            presets: [5, 10, 20, 50, 100],
            placeholder: 'e.g. 5, 20',
        },
        {
            key: 'unique_id',
            labelKey: 'TRANSACTION.FILTER.FIELDS.UNIQUE_ID',
            category: 'GENERAL',
            icon: 'fingerprint',
            type: 'text',
            placeholder: 'e.g. eb6d37ef0815c282769759d6331f2914',
        },
        {
            key: 'archived',
            labelKey: 'TRANSACTION.FILTER.FIELDS.ARCHIVED',
            category: 'GENERAL',
            icon: 'archive',
            type: 'boolean',
            options: ['true', 'false'],
        },

        // ROUTING
        {
            key: 'service._id',
            labelKey: 'TRANSACTION.FILTER.FIELDS.SERVICE_ID',
            category: 'ROUTING',
            icon: 'miscellaneous_services',
            type: 'text',
            placeholder: 'e.g. local-dev, api-gateway',
        },
        {
            key: 'route_name',
            labelKey: 'TRANSACTION.FILTER.FIELDS.ROUTE_NAME',
            category: 'ROUTING',
            icon: 'alt_route',
            type: 'text',
            placeholder: 'e.g. front-req, api-route',
        },
        {
            key: 'upstream._id',
            labelKey: 'TRANSACTION.FILTER.FIELDS.UPSTREAM_ID',
            category: 'ROUTING',
            icon: 'dns',
            type: 'text',
            placeholder: 'e.g. NXGuard_Frontend',
        },

        // NETWORK
        {
            key: 'source.ip',
            labelKey: 'TRANSACTION.FILTER.FIELDS.SOURCE_IP',
            category: 'NETWORK',
            icon: 'travel_explore',
            type: 'text',
            placeholder: 'e.g. 192.168.1.1, 10.0.0.1',
        },
        {
            key: 'source.port',
            labelKey: 'TRANSACTION.FILTER.FIELDS.SOURCE_PORT',
            category: 'NETWORK',
            icon: 'numbers',
            type: 'number',
            placeholder: 'e.g. 443, 8080',
        },
        {
            key: 'geoip.country_code',
            labelKey: 'TRANSACTION.FILTER.FIELDS.GEOIP_COUNTRY',
            category: 'NETWORK',
            icon: 'flag',
            type: 'text',
            presets: ['US', 'BR', 'DE', 'CN', 'RU', 'GB'],
            placeholder: 'e.g. US, BR, CN',
        },
        {
            key: 'destination.host',
            labelKey: 'TRANSACTION.FILTER.FIELDS.DESTINATION_HOST',
            category: 'NETWORK',
            icon: 'hub',
            type: 'text',
            placeholder: 'e.g. nxguard.local, example.com',
        },
        {
            key: 'destination.port',
            labelKey: 'TRANSACTION.FILTER.FIELDS.DESTINATION_PORT',
            category: 'NETWORK',
            icon: 'tag',
            type: 'number',
            presets: [80, 443, 8443, 8080],
        },

        // HTTP
        {
            key: 'http.request.method',
            labelKey: 'TRANSACTION.FILTER.FIELDS.HTTP_METHOD',
            category: 'HTTP',
            icon: 'http',
            type: 'enum',
            options: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'],
        },
        {
            key: 'http.request.uri',
            labelKey: 'TRANSACTION.FILTER.FIELDS.HTTP_URI',
            category: 'HTTP',
            icon: 'link',
            type: 'text',
            placeholder: 'e.g. /api/v1/auth, /login, /nxg/',
        },
        {
            key: 'http.response.status_code',
            labelKey: 'TRANSACTION.FILTER.FIELDS.STATUS_CODE',
            category: 'HTTP',
            icon: 'check_box',
            type: 'number',
            presets: [200, 201, 301, 400, 401, 403, 404, 500, 502, 503],
            placeholder: 'e.g. 200, 403, 500',
        },
        {
            key: 'user_agent.family',
            labelKey: 'TRANSACTION.FILTER.FIELDS.USER_AGENT',
            category: 'HTTP',
            icon: 'devices',
            type: 'text',
            presets: ['Chrome', 'Firefox', 'Safari', 'Edge', 'curl', 'python-requests'],
            placeholder: 'e.g. Chrome, Firefox',
        },

        // SECURITY
        {
            key: 'rate_limit.action',
            labelKey: 'TRANSACTION.FILTER.FIELDS.RATE_LIMIT_ACTION',
            category: 'SECURITY',
            icon: 'timer',
            type: 'enum',
            options: ['allowed', 'delayed', 'rejected'],
        },
        {
            key: 'limit_req_status',
            labelKey: 'TRANSACTION.FILTER.FIELDS.LIMIT_REQ_STATUS',
            category: 'SECURITY',
            icon: 'hourglass_empty',
            type: 'enum',
            options: ['PASSED', 'DELAYED', 'REJECTED'],
        },
        {
            key: 'geoip_status',
            labelKey: 'TRANSACTION.FILTER.FIELDS.GEOIP_STATUS',
            category: 'SECURITY',
            icon: 'public',
            type: 'enum',
            options: ['ALLOW', 'DENY'],
        },
        {
            key: 'rbl_status',
            labelKey: 'TRANSACTION.FILTER.FIELDS.RBL_STATUS',
            category: 'SECURITY',
            icon: 'gavel',
            type: 'enum',
            options: ['ALLOW', 'DENY'],
        },
        {
            key: 'ipxa',
            labelKey: 'TRANSACTION.FILTER.FIELDS.IPXA',
            category: 'SECURITY',
            icon: 'verified_user',
            type: 'enum',
            options: ['success', 'failed'],
        },
        {
            key: 'rule_code',
            labelKey: 'TRANSACTION.FILTER.FIELDS.AUDIT_RULE_CODE',
            category: 'SECURITY',
            icon: 'policy',
            type: 'text',
            presets: ['941100', '942100', '920270', '911100', '949110'],
            placeholder: 'e.g. 941100, 942120',
        },
        {
            key: 'mtls.verified',
            labelKey: 'TRANSACTION.FILTER.FIELDS.MTLS_VERIFIED',
            category: 'SECURITY',
            icon: 'vpn_key',
            type: 'boolean',
            options: ['true', 'false'],
        },

        // SYSTEM
        {
            key: 'server_id',
            labelKey: 'TRANSACTION.FILTER.FIELDS.SERVER_ID',
            category: 'SYSTEM',
            icon: 'dns',
            type: 'text',
            placeholder: 'e.g. c587ee68a057',
        },
    ];

    selectedCategory: string = 'ALL';

    constructor(
        private fb: FormBuilder,
        public dialogRef: MatDialogRef<TransactionFilterDialogComponent>,
        @Inject(MAT_DIALOG_DATA) public data: any
    ) {}

    ngOnInit(): void {
        const initialField = this.fields[0];
        this.filterForm = this.fb.group({
            field: [initialField.key, Validators.required],
            value: [initialField.options ? initialField.options[0] : '', Validators.required],
        });

        this.filterForm.get('field')?.valueChanges.subscribe((fieldKey) => {
            const field = this.getField(fieldKey);
            if (field) {
                if (field.options && field.options.length > 0) {
                    this.filterForm.get('value')?.setValue(field.options[0]);
                } else if (field.presets && field.presets.length > 0) {
                    this.filterForm.get('value')?.setValue('');
                } else {
                    this.filterForm.get('value')?.setValue('');
                }
            }
        });
    }

    get currentField(): FilterFieldOption {
        return this.getField(this.filterForm.get('field')?.value) || this.fields[0];
    }

    getField(key: string): FilterFieldOption | undefined {
        return this.fields.find((f) => f.key === key);
    }

    get filteredFields(): FilterFieldOption[] {
        if (this.selectedCategory === 'ALL') {
            return this.fields;
        }
        return this.fields.filter((f) => f.category === this.selectedCategory);
    }

    onSelectPreset(val: any): void {
        this.filterForm.get('value')?.setValue(val);
    }

    get previewJson(): string {
        const fieldKey = this.filterForm.get('field')?.value;
        let value = this.filterForm.get('value')?.value;

        if (value === null || value === undefined || value === '') {
            return '{}';
        }

        const field = this.getField(fieldKey);
        if (field?.type === 'number') {
            const num = Number(value);
            value = isNaN(num) ? value : num;
        } else if (field?.type === 'boolean') {
            value = value === 'true' || value === true;
        }

        return JSON.stringify({ [fieldKey]: value });
    }

    onCancel(): void {
        this.dialogRef.close();
    }

    onApply(): void {
        if (this.filterForm.invalid) {
            return;
        }
        const jsonStr = this.previewJson;
        if (jsonStr && jsonStr !== '{}') {
            this.dialogRef.close(jsonStr);
        }
    }
}
