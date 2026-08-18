import { CommonModule } from '@angular/common';
import { Component, Inject } from '@angular/core';
import { MAT_SNACK_BAR_DATA, MatSnackBarRef } from '@angular/material/snack-bar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDialog } from '@angular/material/dialog';
import { APIErrorResponse } from 'app/models/shared';
import { ErrorDetailsDialogComponent } from '../error-details-dialog/error-details-dialog.component';

export interface SnackbarData {
    message?: string;
    messages?: string[];
    errorData?: APIErrorResponse;
}

@Component({
    selector: 'app-multi-snackbar',
    standalone: true,
    imports: [CommonModule, MatButtonModule, MatIconModule],
    template: `
        <div class="multi-snackbar">
            <div class="snackbar-content">
                <div *ngIf="data.messages">
                    <div *ngFor="let message of data.messages" class="snackbar-item">
                        {{ message }}
                    </div>
                </div>
                <div *ngIf="data.message && !data.messages" class="snackbar-item">
                    {{ data.message }}
                </div>
            </div>
            <button *ngIf="data.errorData" mat-stroked-button color="warn" class="details-btn" (click)="openDetails()">
                <mat-icon>info</mat-icon>
                Details
            </button>
        </div>
    `,
    styles: [`
        .multi-snackbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            padding: 4px 8px;
            width: 100%;
        }
        .snackbar-content {
            display: flex;
            flex-direction: column;
            gap: 4px;
            flex: 1;
        }
        .snackbar-item {
            padding: 4px 0;
        }
        .details-btn {
            white-space: nowrap;
            display: flex;
            align-items: center;
            gap: 6px;
        }
    `]
})
export class MultiSnackbarComponent {
    constructor(
        public snackBarRef: MatSnackBarRef<MultiSnackbarComponent>,
        @Inject(MAT_SNACK_BAR_DATA) public data: SnackbarData,
        private dialog: MatDialog
    ) {}

    openDetails(): void {
        if (this.data.errorData) {
            this.dialog.open(ErrorDetailsDialogComponent, {
                data: this.data.errorData,
                width: '650px',
                maxWidth: '90vw'
            });
            this.snackBarRef.dismiss();
        }
    }
}