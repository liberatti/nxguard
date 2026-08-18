import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, Inject, OnInit, Optional } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { TranslatePipe } from '@ngx-translate/core';
import { ConfigService } from '../../services/config.service';

export interface ChangeItem {
    _id?: number;
    name: string;
}

@Component({
    selector: 'app-apply-dialog',
    templateUrl: './apply-dialog.component.html',
    styleUrl: './apply-dialog.component.css',
    standalone: true,
    imports: [
        CommonModule,
        MatCardModule,
        MatButtonModule,
        MatDialogModule,
        MatChipsModule,
        MatIconModule,
        MatListModule,
        MatProgressBarModule,
        TranslatePipe
    ],
})
export class ApplyDialogComponent implements OnInit {
    changes: ChangeItem[] = [];
    loadingChanges: boolean = true;
    applying: boolean = false;
    applied: boolean = false;
    success: boolean = false;
    error: string = '';

    constructor(
        public dialogRef: MatDialogRef<ApplyDialogComponent>,
        private configService: ConfigService,
        private cdr: ChangeDetectorRef,
        @Optional() @Inject(MAT_DIALOG_DATA) public data: any
    ) {
        if (data?.changes && Array.isArray(data.changes) && data.changes.length > 0) {
            this.changes = data.changes.map((c: any) => (typeof c === 'string' ? { name: c } : c));
            this.loadingChanges = false;
        }
    }

    ngOnInit(): void {
        this.loadChanges();
    }

    loadChanges(): void {
        if (this.changes.length === 0) {
            this.loadingChanges = true;
        }
        this.configService.getChanges().subscribe({
            next: (res) => {
                if (res && res.data && Array.isArray(res.data)) {
                    this.changes = res.data;
                } else if (Array.isArray(res)) {
                    this.changes = res.map((c: any) => (typeof c === 'string' ? { name: c } : c));
                } else if (res && Array.isArray(res.changes)) {
                    this.changes = res.changes.map((c: any) => (typeof c === 'string' ? { name: c } : c));
                }
                this.loadingChanges = false;
                this.cdr.detectChanges();
            },
            error: () => {
                this.configService.healthCheck().subscribe({
                    next: (data) => {
                        if (data && data.apply_pendding && Array.isArray(data.apply_pendding)) {
                            this.changes = data.apply_pendding.map((name: string) => ({ name }));
                        }
                        this.loadingChanges = false;
                        this.cdr.detectChanges();
                    },
                    error: () => {
                        this.loadingChanges = false;
                        this.cdr.detectChanges();
                    }
                });
            }
        });
    }

    onApply(): void {
        this.applying = true;
        this.applied = false;
        this.success = false;
        this.error = '';
        this.dialogRef.disableClose = true;
        this.cdr.detectChanges();

        this.configService.applyConfig().subscribe({
            next: () => {
                this.applying = false;
                this.applied = true;
                this.success = true;
                this.dialogRef.disableClose = false;
                this.cdr.detectChanges();
            },
            error: (err) => {
                this.applying = false;
                this.applied = true;
                this.success = false;
                this.error = err?.error?.message || err?.message || 'An error occurred during configuration apply';
                this.dialogRef.disableClose = false;
                this.cdr.detectChanges();
            }
        });
    }

    getModuleIcon(name: string): string {
        switch (name) {
            case 'service': return 'alt_route';
            case 'upstream': return 'hub';
            case 'certificate': return 'lock';
            case 'sensor': return 'sensors';
            case 'feed': return 'rss_feed';
            default: return 'settings';
        }
    }

    closeDialog(): void {
        this.dialogRef.close(this.success);
    }
}
