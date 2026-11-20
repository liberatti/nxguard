import { Component, Inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatChipsModule } from '@angular/material/chips';
import { TranslatePipe } from '@ngx-translate/core';

export interface RuleDialogData {
    rule?: any;
    categoryPhase?: number;
    categoryScope?: string;
    existingCodes?: number[];
}

@Component({
    selector: 'app-rule-form-dialog',
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
        MatTabsModule,
        MatTooltipModule,
        MatChipsModule,
        TranslatePipe
    ],
    templateUrl: './rule-form-dialog.component.html',
    styleUrl: './rule-form-dialog.component.css'
})
export class RuleFormDialogComponent implements OnInit {
    isEdit = false;
    selectedTabIndex = 0;

    commonScopes: string[] = [
        'REQUEST_URI',
        'ARGS',
        'REQUEST_HEADERS',
        'REQUEST_COOKIES',
        'REQUEST_BODY',
        'REMOTE_ADDR'
    ];

    actionOptions: string[] = ['block', 'deny', 'drop', 'pass', 'allow', 'redirect'];
    severityOptions: string[] = ['CRITICAL', 'ERROR', 'WARNING', 'NOTICE', 'INFO', 'DEBUG'];
    phaseOptions: { value: number; label: string }[] = [
        { value: 1, label: '1 - Request Headers' },
        { value: 2, label: '2 - Request Body' },
        { value: 3, label: '3 - Response Headers' },
        { value: 4, label: '4 - Response Body' },
        { value: 5, label: '5 - Logging' }
    ];
    operatorOptions: string[] = [
        '@rx',
        '@contains',
        '@streq',
        '@pm',
        '@within',
        '@beginsWith',
        '@endsWith',
        '@eq',
        '@ge',
        '@le',
        '@lt',
        '@gt'
    ];

    form = new FormGroup({
        code: new FormControl<number | null>(null, [Validators.required, Validators.min(1)]),
        action: new FormControl<string>('block', [Validators.required]),
        phase: new FormControl<number>(2, [Validators.required]),
        severity: new FormControl<string>('CRITICAL'),
        msg: new FormControl<string>('', [Validators.required]),
        scope: new FormControl<string>('REQUEST_URI', [Validators.required]),
        operator: new FormControl<string>('@rx'),
        pattern: new FormControl<string>(''),
        tags: new FormControl<string>('custom'),
        comment: new FormControl<string>(''),
        raw: new FormControl<string>('')
    });

    constructor(
        public dialogRef: MatDialogRef<RuleFormDialogComponent>,
        @Inject(MAT_DIALOG_DATA) public data: RuleDialogData
    ) {}

    ngOnInit(): void {
        const defaultPhase = this.data?.categoryPhase || 2;
        this.form.patchValue({ phase: defaultPhase });

        if (this.data?.rule) {
            this.isEdit = true;
            const r = this.data.rule;
            const scopeStr = Array.isArray(r.scope) ? r.scope.join(', ') : (r.scope || 'REQUEST_URI');
            const tagsStr = Array.isArray(r.tags) ? r.tags.join(', ') : (r.tags || '');

            this.form.patchValue({
                code: r.code || (r._id ? Number(r._id) : null),
                action: (r.action || 'block').toLowerCase(),
                phase: r.phase !== undefined ? Number(r.phase) : defaultPhase,
                severity: (r.severity || 'CRITICAL').toUpperCase(),
                msg: r.msg || '',
                scope: scopeStr,
                tags: tagsStr,
                comment: r.comment || '',
                raw: r.raw || ''
            });

            // Extract operator & pattern from raw if available
            this.parseRawRule(r.raw);
        } else {
            // Suggest next available rule code if existingCodes given
            if (this.data?.existingCodes && this.data.existingCodes.length > 0) {
                const maxCode = Math.max(...this.data.existingCodes.filter(c => !isNaN(c)));
                if (maxCode > 0) {
                    this.form.patchValue({ code: maxCode + 1 });
                }
            }
            this.updateAutoRaw();
        }

        // Keep raw in sync if user hasn't manually entered custom raw
        this.form.valueChanges.subscribe(() => {
            if (this.selectedTabIndex === 0 && !this.isEdit) {
                this.updateAutoRaw();
            }
        });
    }

    parseRawRule(raw?: string): void {
        if (!raw) return;
        // Simple regex check: SecRule SCOPE "OPERATOR PATTERN" "..."
        const match = raw.match(/SecRule\s+([^\s"]+)\s+"(@[a-zA-Z0-9]+)\s+([^"]+)"/);
        if (match) {
            this.form.patchValue({
                scope: match[1],
                operator: match[2],
                pattern: match[3]
            }, { emitEvent: false });
        }
    }

    updateAutoRaw(): void {
        const val = this.form.getRawValue();
        const code = val.code || 1001;
        const phase = val.phase || 2;
        const action = val.action || 'block';
        const sev = val.severity || 'CRITICAL';
        const msg = (val.msg || 'Custom rule match').replace(/'/g, "\\'");
        const scope = val.scope || 'REQUEST_URI';
        const op = val.operator || '@rx';
        const pat = val.pattern || '(?i)malicious_payload';
        const tags = (val.tags || '')
            .split(',')
            .map(t => t.trim())
            .filter(Boolean)
            .map(t => `tag:'${t}'`)
            .join(',');

        let actionsStr = `id:${code},phase:${phase},${action},msg:'${msg}',severity:'${sev}'`;
        if (tags) {
            actionsStr += `,${tags}`;
        }

        const autoRaw = `SecRule ${scope} "${op} ${pat}" "${actionsStr}"`;
        this.form.get('raw')?.setValue(autoRaw, { emitEvent: false });
    }

    toggleScopeSuggestion(target: string): void {
        const current = (this.form.get('scope')?.value || '')
            .split(',')
            .map(s => s.trim())
            .filter(Boolean);
        const idx = current.indexOf(target);
        if (idx >= 0) {
            current.splice(idx, 1);
        } else {
            current.push(target);
        }
        this.form.get('scope')?.setValue(current.join(', '));
        this.updateAutoRaw();
    }

    isScopeSelected(target: string): boolean {
        const current = (this.form.get('scope')?.value || '')
            .split(',')
            .map(s => s.trim())
            .filter(Boolean);
        return current.includes(target);
    }

    onSave(): void {
        if (this.form.invalid) {
            this.form.markAllAsTouched();
            return;
        }

        const val = this.form.getRawValue();
        const codeNum = Number(val.code);

        const scopeList = (val.scope || 'REQUEST_URI')
            .split(',')
            .map(s => s.trim())
            .filter(Boolean);

        const tagsList = (val.tags || '')
            .split(',')
            .map(t => t.trim())
            .filter(Boolean);

        let finalRaw = (val.raw || '').trim();
        if (!finalRaw) {
            this.updateAutoRaw();
            finalRaw = this.form.get('raw')?.value || '';
        }

        const result = {
            _id: String(codeNum),
            code: codeNum,
            action: (val.action || 'block').toLowerCase(),
            phase: Number(val.phase),
            severity: (val.severity || 'CRITICAL').toUpperCase(),
            msg: val.msg?.trim() || '',
            scope: scopeList,
            tags: tagsList,
            comment: val.comment?.trim() || '',
            raw: finalRaw,
            schema_type: 'SecRule'
        };

        this.dialogRef.close(result);
    }

    onCancel(): void {
        this.dialogRef.close(null);
    }
}

