import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterModule } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { TranslatePipe, TranslateService } from '@ngx-translate/core';
import { Clipboard } from '@angular/cdk/clipboard';

import { ConfigDiffDialogComponent } from 'app/components/config-diff-dialog/config-diff-dialog.component';
import { ConfirmDialogComponent } from 'app/components/confirm-dialog/confirm-dialog.component';
import { ConfigAuditHistoryItem } from 'app/models/config';
import { ConfigService } from 'app/services/config.service';
import { NotificationService } from 'app/services/notification.service';
import { OAuthService } from 'app/services/oauth.service';

@Component({
    selector: 'app-config-audit',
    standalone: true,
    imports: [
        CommonModule,
        RouterModule,
        TranslatePipe,
        MatCardModule,
        MatButtonModule,
        MatIconModule,
        MatTableModule,
        MatChipsModule,
        MatTooltipModule,
        MatPaginatorModule,
        MatProgressBarModule,
        MatDialogModule,
    ],
    templateUrl: './config-audit.component.html',
    styleUrl: './config-audit.component.css'
})
export class ConfigAuditComponent implements OnInit {
    protected readonly configService = inject(ConfigService);
    protected readonly notificationService = inject(NotificationService);
    protected readonly translate = inject(TranslateService);
    protected readonly dialog = inject(MatDialog);
    protected readonly oauth = inject(OAuthService);
    private readonly clipboard = inject(Clipboard);

    readonly displayedColumns: string[] = ['status', 'scn', 'created_at', 'hash', 'counts', 'patch', 'actions'];

    readonly history = signal<ConfigAuditHistoryItem[]>([]);
    readonly total = signal<number>(0);
    readonly page = signal<number>(1);
    readonly perPage = signal<number>(10);
    readonly isLoading = signal<boolean>(false);
    readonly activeScn = signal<string | null>(null);

    ngOnInit(): void {
        this.loadHistory();
    }

    loadHistory(): void {
        this.isLoading.set(true);
        this.configService.getHistory(this.page(), this.perPage()).subscribe({
            next: (res: any) => {
                this.isLoading.set(false);
                const items: ConfigAuditHistoryItem[] = res?.data || [];
                this.history.set(items);
                this.total.set(res?.total || 0);
                this.activeScn.set(res?.active_scn || null);
            },
            error: (err: any) => {
                this.isLoading.set(false);
                this.notificationService.openErrorSnackBar(err?.error || err);
            }
        });
    }

    openDiffDialog(item: ConfigAuditHistoryItem): void {
        const dialogRef = this.dialog.open(ConfigDiffDialogComponent, {
            data: {
                item: item,
                activeScn: this.activeScn()
            },
            width: '920px',
            maxWidth: '96vw',
            panelClass: 'config-diff-dialog-panel'
        });

        dialogRef.afterClosed().subscribe((reloaded: boolean) => {
            if (reloaded) {
                this.loadHistory();
            }
        });
    }

    confirmRestore(item: ConfigAuditHistoryItem): void {
        const dialogRef = this.dialog.open(ConfirmDialogComponent, {
            data: {
                title: this.translate.instant('CONFIG_AUDIT.CONFIRM_RESTORE_TITLE'),
                message: this.translate.instant('CONFIG_AUDIT.CONFIRM_RESTORE_MSG', {
                    scn: item.scn,
                    date: item.created_at || ''
                })
            }
        });

        dialogRef.afterClosed().subscribe((confirmed: boolean) => {
            if (confirmed) {
                this.isLoading.set(true);
                this.configService.applyHistoryVersion(item.scn).subscribe({
                    next: () => {
                        this.isLoading.set(false);
                        const msg = this.translate.instant('CONFIG_AUDIT.RESTORE_SUCCESS', { scn: item.scn });
                        this.notificationService.openSnackBar(msg);
                        this.loadHistory();
                    },
                    error: (err: any) => {
                        this.isLoading.set(false);
                        this.notificationService.openErrorSnackBar(err?.error || err);
                    }
                });
            }
        });
    }

    copyHash(hash?: string): void {
        if (!hash) return;
        this.clipboard.copy(hash);
        const msg = this.translate.instant('CONFIG_AUDIT.HASH_COPIED') || 'Hash copied to clipboard';
        this.notificationService.openSnackBar(msg);
    }

    downloadVersion(item: ConfigAuditHistoryItem): void {
        this.configService.getVersionDiff(item.scn).subscribe({
            next: (diff: any) => {
                const content = diff?.target?.raw_data || item;
                const blob = new Blob([JSON.stringify(content, null, 2)], { type: 'application/json' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `nxguard-config-${item.scn}.json`;
                a.click();
                window.URL.revokeObjectURL(url);
            },
            error: (err: any) => {
                this.notificationService.openErrorSnackBar(err?.error || err);
            }
        });
    }

    onPageChange(event: PageEvent): void {
        this.page.set(event.pageIndex + 1);
        this.perPage.set(event.pageSize);
        this.loadHistory();
    }
}
