import { Component, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import {
    MAT_DIALOG_DATA,
    MatDialogActions,
    MatDialogContent,
    MatDialogRef,
    MatDialogTitle,
} from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { Clipboard, ClipboardModule } from '@angular/cdk/clipboard';
import { TranslatePipe } from '@ngx-translate/core';
import { HighlightModule } from 'ngx-highlightjs';
import { MatExpansionModule } from '@angular/material/expansion';
import { TransactionLog } from '../../models/transaction';

@Component({
    selector: 'app-rbl-details-dialog',
    templateUrl: './rbl-details-dialog.component.html',
    styleUrl: './rbl-details-dialog.component.css',
    standalone: true,
    imports: [
        CommonModule,
        MatCardModule,
        MatButtonModule,
        MatDialogTitle,
        MatDialogContent,
        MatDialogActions,
        MatIconModule,
        MatTooltipModule,
        MatSnackBarModule,
        ClipboardModule,
        TranslatePipe,
        HighlightModule,
        MatExpansionModule,
    ],
})
export class RblDetailsDialogComponent {
    copiedIp: boolean = false;
    copiedJson: boolean = false;

    constructor(
        @Inject(MAT_DIALOG_DATA) public data: TransactionLog,
        public dialogRef: MatDialogRef<RblDetailsDialogComponent>,
        private clipboard: Clipboard,
        private snackBar: MatSnackBar
    ) {}

    get ipAddress(): string {
        return this.data?.source?.ip || this.data?.source?.geo?.ip || '-';
    }

    get rblAction(): string {
        return this.data?.rbl_status || this.data?.reputation?.action || '-';
    }

    get riskScore(): number {
        return this.data?.reputation?.score ?? (this.data?.score ?? 0);
    }

    get isTrusted(): boolean {
        return !!this.data?.reputation?.trusted;
    }

    get matchedFeeds(): string[] {
        const feeds = this.data?.reputation?.feeds || (this.data?.reputation?.feed ? [this.data.reputation.feed] : []);
        return feeds;
    }

    get ipxa(): string {
        return this.data?.ipxa || '-';
    }

    get rawReputationData(): any {
        return {
            ip: this.ipAddress,
            rbl_status: this.rblAction,
            risk_score: this.riskScore,
            trusted: this.isTrusted,
            matched_feeds: this.matchedFeeds,
            reputation_context: this.data?.reputation || null,
            ipxa: this.data?.ipxa || null,
            source_port: this.data?.source?.port || null,
            destination: this.data?.destination || null,
            unique_id: this.data?.unique_id || null,
        };
    }

    get rawReputationJson(): string {
        return JSON.stringify(this.rawReputationData, null, 4);
    }

    copyIp(): void {
        if (this.ipAddress && this.ipAddress !== '-') {
            this.clipboard.copy(this.ipAddress);
            this.copiedIp = true;
            this.snackBar.open('IP copied to clipboard', 'OK', {
                duration: 2000,
                horizontalPosition: 'center',
                verticalPosition: 'bottom',
            });
            setTimeout(() => {
                this.copiedIp = false;
            }, 2000);
        }
    }

    copyJson(): void {
        this.clipboard.copy(this.rawReputationJson);
        this.copiedJson = true;
        this.snackBar.open('Reputation data copied to clipboard', 'OK', {
            duration: 2000,
            horizontalPosition: 'center',
            verticalPosition: 'bottom',
        });
        setTimeout(() => {
            this.copiedJson = false;
        }, 2000);
    }

    onDismiss(): void {
        this.dialogRef.close(false);
    }
}
