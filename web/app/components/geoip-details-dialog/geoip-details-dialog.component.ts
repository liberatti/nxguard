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
    selector: 'app-geoip-details-dialog',
    templateUrl: './geoip-details-dialog.component.html',
    styleUrl: './geoip-details-dialog.component.css',
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
export class GeoipDetailsDialogComponent {
    copiedIp: boolean = false;
    copiedJson: boolean = false;

    constructor(
        @Inject(MAT_DIALOG_DATA) public data: TransactionLog,
        public dialogRef: MatDialogRef<GeoipDetailsDialogComponent>,
        private clipboard: Clipboard,
        private snackBar: MatSnackBar
    ) {}

    get ipAddress(): string {
        return this.data?.source?.ip || this.data?.source?.geo?.ip || this.data?.source?.geo?.addr || '-';
    }

    get countryCode(): string {
        const c = this.data?.source?.geo?.country || (this.data as any)?.geoip?.country_code;
        return (c && c !== '--') ? c : '';
    }

    get organization(): string {
        return this.data?.source?.geo?.organization || '-';
    }

    get asn(): string {
        return this.data?.source?.geo?.ans_number || '-';
    }

    get ipRange(): string {
        const start = this.data?.source?.geo?.range_start;
        const end = this.data?.source?.geo?.range_end;
        if (start && end) return `${start} - ${end}`;
        return '-';
    }

    get geoipAction(): string {
        return this.data?.geoip_status || (this.data as any)?.geoip?.action || '-';
    }

    get ipxa(): string {
        return (this.data as any)?.ipxa || '-';
    }

    get rawGeoData(): any {
        return {
            ip: this.ipAddress,
            country: this.countryCode || '--',
            geoip_status: this.geoipAction,
            source_geo: this.data?.source?.geo || null,
            geoip_context: (this.data as any)?.geoip || null,
            ipxa: (this.data as any)?.ipxa || null,
            source_port: this.data?.source?.port || null,
            destination: this.data?.destination || null,
            unique_id: this.data?.unique_id || null,
        };
    }

    get rawGeoJson(): string {
        return JSON.stringify(this.rawGeoData, null, 4);
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
        this.clipboard.copy(this.rawGeoJson);
        this.copiedJson = true;
        this.snackBar.open('GeoIP data copied to clipboard', 'OK', {
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
