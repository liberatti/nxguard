import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
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

import { RuleCategory } from '../../models/sensor';
import { RuleCategoryService } from '../../services/sensor.service';
import { NotificationService } from '../../services/notification.service';
import { OAuthService } from '../../services/oauth.service';

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
        MatProgressBarModule
    ],
    templateUrl: './rulecat-form.component.html',
    styleUrl: './rulecat-form.component.css'
})
export class RuleCategoryFormComponent implements OnInit {
    isAddMode = true;
    isLoading = false;
    submitted = false;

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
        system: new FormControl<boolean>(false)
    });

    constructor(
        private route: ActivatedRoute,
        private router: Router,
        private ruleCatService: RuleCategoryService,
        private notificationService: NotificationService,
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
                        this.form.patchValue({
                            _id: data._id || '',
                            name: data.name || '',
                            phase: data.phase !== undefined ? data.phase : 2,
                            scope: data.scope || (data.phase && data.phase >= 4 ? 'response' : 'request'),
                            seq: data.seq !== undefined ? data.seq : null,
                            file: data.file || '',
                            system: !!data.system,
                            provider: data.provider || ''
                        });
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
        if (this.form.invalid) {
            return;
        }

        const raw = this.form.getRawValue();
        const payload: Partial<RuleCategory> = {
            name: raw.name.trim(),
            phase: Number(raw.phase),
            scope: raw.scope,
            system: !!raw.system,
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
}
