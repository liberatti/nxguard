import { Component, Inject, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import {
    MAT_DIALOG_DATA,
    MatDialog,
    MatDialogActions,
    MatDialogContent,
    MatDialogRef,
} from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Clipboard, ClipboardModule } from '@angular/cdk/clipboard';
import { HighlightModule } from 'ngx-highlightjs';
import { TranslatePipe, TranslateService } from '@ngx-translate/core';

import { ConfigAuditHistoryItem, ConfigVersionDiff, DeepDiffChange, JsonPatchOperation } from 'app/models/config';
import { ConfigService } from 'app/services/config.service';
import { NotificationService } from 'app/services/notification.service';
import { ConfirmDialogComponent } from '../confirm-dialog/confirm-dialog.component';

export interface ConfigDiffDialogData {
    item: ConfigAuditHistoryItem;
    diff?: ConfigVersionDiff;
    activeScn?: string | null;
}

@Component({
    selector: 'app-config-diff-dialog',
    templateUrl: './config-diff-dialog.component.html',
    styleUrl: './config-diff-dialog.component.css',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        MatCardModule,
        MatButtonModule,
        MatChipsModule,
        MatDialogContent,
        MatDialogActions,
        MatTabsModule,
        MatIconModule,
        MatTooltipModule,
        MatSnackBarModule,
        MatProgressBarModule,
        MatProgressSpinnerModule,
        ClipboardModule,
        HighlightModule,
        TranslatePipe,
    ],
})
export class ConfigDiffDialogComponent implements OnInit {
    private readonly configService = inject(ConfigService);
    private readonly notificationService = inject(NotificationService);
    private readonly snackBar = inject(MatSnackBar);
    private readonly clipboard = inject(Clipboard);
    private readonly translate = inject(TranslateService);
    private readonly dialog = inject(MatDialog);

    readonly item: ConfigAuditHistoryItem;
    readonly activeScn: string | null;
    readonly diff = signal<ConfigVersionDiff | null>(null);
    readonly isLoading = signal<boolean>(false);
    readonly selectedOpFilter = signal<string>('all');
    readonly selectedSemanticFilter = signal<string>('all');
    readonly semanticSearchQuery = signal<string>('');
    readonly isApplying = signal<boolean>(false);
    readonly copiedHash = signal<boolean>(false);
    readonly copiedPatch = signal<boolean>(false);
    readonly showFormattedCanonical = signal<boolean>(true);

    constructor(
        @Inject(MAT_DIALOG_DATA) public data: ConfigDiffDialogData,
        public dialogRef: MatDialogRef<ConfigDiffDialogComponent>
    ) {
        this.item = data.item;
        this.activeScn = data.activeScn || null;
        if (data.diff) {
            this.diff.set(data.diff);
        }
    }

    ngOnInit(): void {
        if (!this.diff()) {
            this.loadDiff();
        }
    }

    loadDiff(): void {
        this.isLoading.set(true);
        this.configService.getVersionDiff(this.item.scn).subscribe({
            next: (d: ConfigVersionDiff) => {
                this.isLoading.set(false);
                this.diff.set(d);
            },
            error: (err: any) => {
                this.isLoading.set(false);
                this.notificationService.openErrorSnackBar(err?.error || err);
            }
        });
    }

    get deepdiffChanges(): DeepDiffChange[] {
        const d = this.diff();
        if (!d || !d.deepdiff || !d.deepdiff.changes) return [];
        let list = d.deepdiff.changes;
        const filter = this.selectedSemanticFilter();
        if (filter !== 'all') {
            list = list.filter(c => c.type === filter);
        }
        const query = this.semanticSearchQuery().trim().toLowerCase();
        if (query) {
            list = list.filter(c =>
                (c.human_path && c.human_path.toLowerCase().includes(query)) ||
                (c.path && c.path.toLowerCase().includes(query))
            );
        }
        return list;
    }

    get deepdiffRawJson(): string {
        const d = this.diff();
        if (!d || !d.deepdiff || !d.deepdiff.raw) return '{}';
        return JSON.stringify(d.deepdiff.raw, null, 2);
    }

    get filteredOperations(): JsonPatchOperation[] {
        const d = this.diff();
        if (!d || !d.rfc6902_patch) return [];
        const filter = this.selectedOpFilter();
        if (filter === 'all') return d.rfc6902_patch;
        return d.rfc6902_patch.filter(op => op.op === filter);
    }

    get rawJson(): string {
        const d = this.diff();
        if (!d || !d.target || !d.target.raw_data) return '{}';
        return JSON.stringify(d.target.raw_data, null, 2);
    }

    get canonicalJson(): string {
        const d = this.diff();
        if (!d || !d.target) return '';
        if (!this.showFormattedCanonical()) {
            return d.target.canonical_json || '';
        }
        if (d.target.raw_data) {
            try {
                return JSON.stringify(d.target.raw_data, null, 2);
            } catch {}
        }
        if (d.target.canonical_json) {
            try {
                return JSON.stringify(JSON.parse(d.target.canonical_json), null, 2);
            } catch {
                return d.target.canonical_json;
            }
        }
        return '';
    }

    get patchJson(): string {
        const d = this.diff();
        if (!d || !d.rfc6902_patch) return '[]';
        return JSON.stringify(d.rfc6902_patch, null, 2);
    }

    copyText(text: string, type: 'hash' | 'patch'): void {
        this.clipboard.copy(text);
        if (type === 'hash') {
            this.copiedHash.set(true);
            setTimeout(() => this.copiedHash.set(false), 2000);
        } else {
            this.copiedPatch.set(true);
            setTimeout(() => this.copiedPatch.set(false), 2000);
        }
        const msg = type === 'hash'
            ? this.translate.instant('CONFIG_AUDIT.HASH_COPIED') || 'Hash copied to clipboard'
            : this.translate.instant('CONFIG_AUDIT.PATCH_COPIED') || 'Patch JSON copied to clipboard';
        this.snackBar.open(msg, 'OK', { duration: 2500, horizontalPosition: 'center', verticalPosition: 'bottom' });
    }

    formatValue(val: any): string {
        if (val === undefined) return '';
        if (typeof val === 'object') {
            return JSON.stringify(val, null, 2);
        }
        return String(val);
    }

    confirmRestore(): void {
        const dialogRef = this.dialog.open(ConfirmDialogComponent, {
            data: {
                title: this.translate.instant('CONFIG_AUDIT.CONFIRM_RESTORE_TITLE'),
                message: this.translate.instant('CONFIG_AUDIT.CONFIRM_RESTORE_MSG', {
                    scn: this.item.scn,
                    date: this.item.created_at || ''
                })
            }
        });

        dialogRef.afterClosed().subscribe((confirmed: boolean) => {
            if (confirmed) {
                this.isApplying.set(true);
                this.configService.applyHistoryVersion(this.item.scn).subscribe({
                    next: () => {
                        this.isApplying.set(false);
                        const msg = this.translate.instant('CONFIG_AUDIT.RESTORE_SUCCESS', { scn: this.item.scn });
                        this.notificationService.openSnackBar(msg);
                        this.dialogRef.close(true);
                    },
                    error: (err: any) => {
                        this.isApplying.set(false);
                        this.notificationService.openErrorSnackBar(err?.error || err);
                    }
                });
            }
        });
    }

    downloadVersion(): void {
        const d = this.diff();
        const content = d?.target?.raw_data || this.item;
        const blob = new Blob([JSON.stringify(content, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `nxguard-config-${this.item.scn}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
    }

    onDismiss(): void {
        this.dialogRef.close(false);
    }
}
