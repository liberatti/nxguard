import { Component, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import {
    MAT_DIALOG_DATA,
    MatDialogActions,
    MatDialogContent,
    MatDialogRef,
    MatDialogTitle,
} from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatTabsModule } from '@angular/material/tabs';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { Clipboard, ClipboardModule } from '@angular/cdk/clipboard';
import { HighlightModule } from 'ngx-highlightjs';

@Component({
    selector: 'app-rule-details-dialog',
    templateUrl: './rule-details-dialog.component.html',
    styleUrl: './rule-details-dialog.component.css',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        MatFormFieldModule,
        MatInputModule,
        MatCardModule,
        MatButtonModule,
        MatDialogTitle,
        MatDialogContent,
        MatDialogActions,
        MatTabsModule,
        MatIconModule,
        MatTooltipModule,
        MatSnackBarModule,
        ClipboardModule,
        HighlightModule,
    ],
})
export class RuleDetailsDialogComponent {
    copied: boolean = false;

    constructor(
        @Inject(MAT_DIALOG_DATA) public data: any,
        public dialogRef: MatDialogRef<RuleDetailsDialogComponent>,
        private clipboard: Clipboard,
        private snackBar: MatSnackBar
    ) {}

    get jsonData(): string {
        return JSON.stringify(this.data, null, 4);
    }

    copyToClipboard(): void {
        this.clipboard.copy(this.jsonData);
        this.copied = true;
        this.snackBar.open('Rule JSON copied to clipboard!', 'OK', {
            duration: 2500,
            horizontalPosition: 'center',
            verticalPosition: 'bottom',
        });
        setTimeout(() => {
            this.copied = false;
        }, 2000);
    }

    onDismiss(): void {
        this.dialogRef.close(false);
    }
}