import { Component, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';

import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';

import { RuleCategory } from '../../models/sensor';
import { RuleCategoryService } from '../../services/sensor.service';
import { NotificationService } from '../../services/notification.service';
import { OAuthService } from '../../services/oauth.service';
import { RuleDetailsDialogComponent } from '../../components/rule-details-dialog/rule-details-dialog.component';
import { RuleFormDialogComponent } from '../../components/rule-form-dialog/rule-form-dialog.component';

export interface PhaseOption {
    value: number;
    labelKey: string;
    scope: string;
}

@Component({
    selector: 'app-rulecat-form',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        ReactiveFormsModule,
        RouterModule,
        TranslatePipe,
        MatCardModule,
        MatButtonModule,
        MatIconModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatSlideToggleModule,
        MatTooltipModule,
        MatChipsModule,
        MatProgressBarModule,
        MatTabsModule,
        MatTableModule,
        MatPaginatorModule,
        MatSortModule,
        MatDialogModule
    ],
    templateUrl: './rulecat-form.component.html',
    styleUrl: './rulecat-form.component.css'
})
export class RuleCategoryFormComponent implements OnInit {
    isAddMode = true;
    isLoading = false;
    submitted = false;

    rules: any[] = [];
    ruleDS: MatTableDataSource<any> = new MatTableDataSource<any>([]);
    ruleDC: string[] = ['code', 'action', 'phase', 'severity', 'description', 'actions'];
    ruleSearchQuery: string = '';
    pageSizeOptions: number[] = [10, 25, 50, 100];

    @ViewChild(MatPaginator) paginator!: MatPaginator;
    @ViewChild(MatSort) sort!: MatSort;

    phases: PhaseOption[] = [
        { value: 1, labelKey: 'RULECAT.PHASES.1', scope: 'request' },
        { value: 2, labelKey: 'RULECAT.PHASES.2', scope: 'request' },
        { value: 3, labelKey: 'RULECAT.PHASES.3', scope: 'request' },
        { value: 4, labelKey: 'RULECAT.PHASES.4', scope: 'response' },
        { value: 5, labelKey: 'RULECAT.PHASES.5', scope: 'response' },
        { value: 6, labelKey: 'RULECAT.PHASES.6', scope: 'response' }
    ];

    scopes: string[] = ['request', 'response'];

    get selectedPhase(): PhaseOption | undefined {
        const val = this.form.get('phase')?.value;
        return this.phases.find(p => p.value === Number(val));
    }

    get isUserCategory(): boolean {
        return this.isAddMode || this.form.get('srctype')?.value === 'user';
    }

    get isFeedCategory(): boolean {
        return !this.isAddMode && this.form.get('srctype')?.value === 'feed';
    }

    form = new FormGroup({
        _id: new FormControl<string>(''),
        name: new FormControl<string>('', {
            nonNullable: true,
            validators: [Validators.required, Validators.minLength(3)]
        }),
        phase: new FormControl<number>(2, {
            nonNullable: true,
            validators: [Validators.required]
        }),
        scope: new FormControl<string>('request', { nonNullable: true }),
        seq: new FormControl<number | null>(null),
        file: new FormControl<string>(''),
        provider: new FormControl<string>(''),
        srctype: new FormControl<string>('user'),
        system: new FormControl<boolean>(false)
    });

    constructor(
        private route: ActivatedRoute,
        private router: Router,
        private ruleCatService: RuleCategoryService,
        private notificationService: NotificationService,
        private dialog: MatDialog,
        protected oauth: OAuthService
    ) {}

    ngOnInit(): void {
        const id = this.route.snapshot.params['id'];
        this.isAddMode = !id;

        if (!this.oauth.isRole('superuser')) {
            this.form.disable();
        }

        if (!this.isAddMode && id) {
            this.isLoading = true;
            this.ruleCatService.getById(id).subscribe({
                next: (res: any) => {
                    const data: RuleCategory = (res && res.data) ? res.data : res;
                    if (data) {
                        const srctype = data.srctype || 'feed';
                        this.form.patchValue({
                            _id: data._id || '',
                            name: data.name || '',
                            phase: data.phase !== undefined ? data.phase : 2,
                            scope: data.scope || (data.phase && data.phase >= 4 ? 'response' : 'request'),
                            seq: data.seq !== undefined ? data.seq : null,
                            file: data.file || '',
                            system: !!data.system,
                            provider: data.provider || '',
                            srctype: srctype
                        });

                        // Permitir editar apenas categoria user; categoria feed deve ser apenas visualização
                        if (srctype === 'feed') {
                            this.form.disable();
                        }

                        if (data.rules && Array.isArray(data.rules)) {
                            this.rules = data.rules.map(r => this.normalizeRule(r));
                            this.ruleDS.data = this.rules;
                            this.setupRuleFilterPredicate();
                            setTimeout(() => {
                                if (this.paginator) {
                                    this.ruleDS.paginator = this.paginator;
                                }
                                if (this.sort) {
                                    this.ruleDS.sort = this.sort;
                                }
                            });
                        }
                    }
                    this.isLoading = false;
                },
                error: () => {
                    this.isLoading = false;
                    this.router.navigate(['/rulecat']);
                }
            });
        }

        // Auto-synchronize default scope and file when phase changes
        this.form.get('phase')?.valueChanges.subscribe((p: number) => {
            if (this.isAddMode) {
                const targetScope = p >= 4 ? 'response' : 'request';
                this.form.get('scope')?.setValue(targetScope);
                this.suggestFilename();
            }
        });

        // Auto-suggest file name when name or id changes if in add mode
        this.form.get('name')?.valueChanges.subscribe(() => {
            if (this.isAddMode) {
                this.suggestFilename();
            }
        });
    }

    suggestFilename(): void {
        const nameVal = this.form.get('name')?.value || '';
        const scopeVal = (this.form.get('scope')?.value || 'request').toUpperCase();
        if (nameVal && !this.form.get('file')?.dirty) {
            this.form.get('file')?.setValue(`${scopeVal}-${nameVal}.conf`);
        }
    }

    onSubmit(): void {
        this.submitted = true;
        if (this.form.invalid || !this.isUserCategory) {
            return;
        }

        const raw = this.form.getRawValue();
        const payload: Partial<RuleCategory> = {
            name: raw.name.trim(),
            phase: Number(raw.phase),
            scope: raw.scope,
            system: !!raw.system,
            srctype: 'user',
            provider: raw.provider?.trim() || 'user',
            rules: this.rules
        };

        if (raw._id && raw._id.trim()) {
            payload._id = raw._id.trim();
        }
        if (raw.seq !== null && raw.seq !== undefined) {
            payload.seq = Number(raw.seq);
        }
        if (raw.file && raw.file.trim()) {
            payload.file = raw.file.trim();
        }

        this.isLoading = true;
        if (this.isAddMode) {
            this.ruleCatService.save(payload).subscribe({
                next: () => {
                    this.isLoading = false;
                    this.notificationService.openSnackBar('RULECAT.NOTIFICATIONS.SAVED');
                    this.router.navigate(['/rulecat']);
                },
                error: () => {
                    this.isLoading = false;
                }
            });
        } else {
            const catId = raw._id || this.route.snapshot.params['id'];
            this.ruleCatService.update(catId, payload).subscribe({
                next: () => {
                    this.isLoading = false;
                    this.notificationService.openSnackBar('RULECAT.NOTIFICATIONS.UPDATED');
                    this.router.navigate(['/rulecat']);
                },
                error: () => {
                    this.isLoading = false;
                }
            });
        }
    }

    normalizeRule(rule: any): any {
        const cleanStr = (s?: string | null) => {
            if (!s) return '';
            return String(s).trim().replace(/^['"]|['"]$/g, '');
        };
        return {
            ...rule,
            code: rule.code || (rule._id ? Number(rule._id) : 0),
            msg: cleanStr(rule.msg),
            severity: cleanStr(rule.severity).toUpperCase(),
            action: (rule.action || 'pass').toLowerCase(),
            phase: rule.phase !== undefined ? rule.phase : 1,
            comment: (rule.comment || '').trim(),
            raw: rule.raw || '',
            tags: Array.isArray(rule.tags) ? rule.tags : []
        };
    }

    setupRuleFilterPredicate(): void {
        this.ruleDS.filterPredicate = (data: any, filter: string) => {
            const term = (filter || '').trim().toLowerCase();
            if (!term) return true;
            const codeStr = String(data.code || data._id || '');
            const msgStr = (data.msg || '').toLowerCase();
            const commentStr = (data.comment || '').toLowerCase();
            const sevStr = (data.severity || '').toLowerCase();
            const actionStr = (data.action || '').toLowerCase();
            const tagsStr = (data.tags || []).join(' ').toLowerCase();
            const rawStr = (data.raw || '').toLowerCase();
            return (
                codeStr.includes(term) ||
                msgStr.includes(term) ||
                commentStr.includes(term) ||
                sevStr.includes(term) ||
                actionStr.includes(term) ||
                tagsStr.includes(term) ||
                rawStr.includes(term)
            );
        };
    }

    applyRuleFilter(): void {
        this.setupRuleFilterPredicate();
        this.ruleDS.filter = (this.ruleSearchQuery || '').trim().toLowerCase();
        if (this.ruleDS.paginator) {
            this.ruleDS.paginator.firstPage();
        }
    }

    clearRuleFilter(): void {
        this.ruleSearchQuery = '';
        this.applyRuleFilter();
    }

    openRawRule(rule: any): void {
        this.dialog.open(RuleDetailsDialogComponent, {
            data: {
                ...rule,
                initialTab: 'raw'
            },
            width: '860px',
            maxWidth: '94vw'
        });
    }

    openCreateRule(): void {
        const dialogRef = this.dialog.open(RuleFormDialogComponent, {
            data: {
                categoryPhase: Number(this.form.get('phase')?.value) || 2,
                categoryScope: this.form.get('scope')?.value || 'request',
                existingCodes: this.rules.map(r => r.code)
            },
            width: '820px',
            maxWidth: '94vw'
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                this.rules = [this.normalizeRule(result), ...this.rules];
                this.ruleDS.data = this.rules;
                this.form.markAsDirty();
            }
        });
    }

    openEditRule(rule: any): void {
        const dialogRef = this.dialog.open(RuleFormDialogComponent, {
            data: {
                rule: { ...rule },
                categoryPhase: Number(this.form.get('phase')?.value) || 2,
                categoryScope: this.form.get('scope')?.value || 'request',
                existingCodes: this.rules.map(r => r.code)
            },
            width: '820px',
            maxWidth: '94vw'
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                const idx = this.rules.findIndex(r => r.code === rule.code);
                if (idx >= 0) {
                    this.rules[idx] = this.normalizeRule(result);
                } else {
                    this.rules.unshift(this.normalizeRule(result));
                }
                this.rules = [...this.rules];
                this.ruleDS.data = this.rules;
                this.form.markAsDirty();
            }
        });
    }

    removeRule(rule: any): void {
        this.rules = this.rules.filter(r => r.code !== rule.code);
        this.ruleDS.data = this.rules;
        this.form.markAsDirty();
    }

    getSeverityClass(severity?: string): string {
        switch ((severity || '').toUpperCase()) {
            case 'CRITICAL':
            case 'EMERGENCY':
                return 'sev-critical';
            case 'ERROR':
            case 'ALERT':
                return 'sev-error';
            case 'WARNING':
                return 'sev-warning';
            case 'NOTICE':
                return 'sev-notice';
            case 'INFO':
            case 'DEBUG':
            default:
                return 'sev-info';
        }
    }

    getActionClass(action?: string): string {
        switch ((action || '').toLowerCase()) {
            case 'block':
            case 'deny':
            case 'drop':
                return 'action-block';
            case 'allow':
            case 'pass':
                return 'action-pass';
            default:
                return 'action-other';
        }
    }
}
