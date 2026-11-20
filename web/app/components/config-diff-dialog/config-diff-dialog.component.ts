import { Component, Inject, OnInit, ViewChild, inject, signal } from '@angular/core';
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
import { MatExpansionModule, MatAccordion } from '@angular/material/expansion';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Clipboard, ClipboardModule } from '@angular/cdk/clipboard';
import { TranslatePipe, TranslateService } from '@ngx-translate/core';

import { ConfigAuditHistoryItem, ConfigVersionDiff, DeepDiffChange } from 'app/models/config';
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
        MatExpansionModule,
        MatIconModule,
        MatTooltipModule,
        MatSnackBarModule,
        MatProgressBarModule,
        MatProgressSpinnerModule,
        ClipboardModule,
        TranslatePipe,
    ],
})
export class ConfigDiffDialogComponent implements OnInit {
    @ViewChild(MatAccordion) accordion?: MatAccordion;

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
    readonly selectedSemanticFilter = signal<string>('all');
    readonly semanticSearchQuery = signal<string>('');
    readonly isApplying = signal<boolean>(false);
    readonly copiedHash = signal<boolean>(false);
    readonly allExpanded = signal<boolean>(true);

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

    expandAll(): void {
        this.allExpanded.set(true);
        this.accordion?.openAll();
    }

    collapseAll(): void {
        this.allExpanded.set(false);
        this.accordion?.closeAll();
    }

    copyText(text: string): void {
        this.clipboard.copy(text);
        this.copiedHash.set(true);
        setTimeout(() => this.copiedHash.set(false), 2000);
        const msg = this.translate.instant('CONFIG_AUDIT.HASH_COPIED') || 'Hash copied to clipboard';
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
