import { Component, Inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatExpansionModule } from '@angular/material/expansion';
import { TranslatePipe } from '@ngx-translate/core';
import { APIErrorResponse } from 'app/models/shared';

export interface FieldError {
    field: string;
    messages: string[];
}

@Component({
    selector: 'app-error-details-dialog',
    standalone: true,
    imports: [
        CommonModule,
        MatDialogModule,
        MatButtonModule,
        MatIconModule,
        MatExpansionModule,
        TranslatePipe
    ],
    templateUrl: './error-details-dialog.component.html',
    styleUrls: ['./error-details-dialog.component.css']
})
export class ErrorDetailsDialogComponent implements OnInit {
    fieldErrors: FieldError[] = [];

    constructor(
        public dialogRef: MatDialogRef<ErrorDetailsDialogComponent>,
        @Inject(MAT_DIALOG_DATA) public data: APIErrorResponse
    ) {}

    ngOnInit(): void {
        if (this.data && this.data.details) {
            this.fieldErrors = this.parseValidationErrors(this.data.details);
        }
    }

    get rawJson(): string {
        return JSON.stringify(this.data, null, 2);
    }

    onClose(): void {
        this.dialogRef.close();
    }

    private parseValidationErrors(details: any, prefix = ''): FieldError[] {
        let result: FieldError[] = [];
        if (!details) return result;

        if (typeof details === 'string') {
            result.push({ field: 'Error', messages: [details] });
            return result;
        }

        if (Array.isArray(details)) {
            result.push({ field: prefix || 'General', messages: details.map(d => String(d)) });
            return result;
        }

        if (typeof details === 'object' && details !== null) {
            for (const key of Object.keys(details)) {
                const val = details[key];
                const currentPath = prefix ? `${prefix}.${key}` : key;

                if (Array.isArray(val)) {
                    result.push({ field: currentPath, messages: val.map(m => String(m)) });
                } else if (typeof val === 'object' && val !== null) {
                    result = result.concat(this.parseValidationErrors(val, currentPath));
                } else if (val) {
                    result.push({ field: currentPath, messages: [String(val)] });
                }
            }
        }
        return result;
    }
}
