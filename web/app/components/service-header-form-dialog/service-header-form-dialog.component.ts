import { Component, Inject, OnInit, Optional } from '@angular/core';
import {
    MAT_DIALOG_DATA,
    MatDialogActions,
    MatDialogContent,
    MatDialogRef,
    MatDialogTitle
} from '@angular/material/dialog';
import { AbstractControl, FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Header } from 'app/models/service';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
    selector: 'app-service-header-form-dialog',
    templateUrl: './service-header-form-dialog.component.html',
    styleUrl: './service-header-form-dialog.component.css',
    standalone: true,
    imports: [
        ReactiveFormsModule,
        CommonModule,
        FormsModule,
        MatCardModule,
        MatButtonModule,
        MatDialogTitle,
        MatDialogContent,
        MatDialogActions,
        MatFormFieldModule,
        MatInputModule,
        MatIconModule,
        MatTooltipModule,
        TranslatePipe
    ],
})
export class ServiceHeaderFormDialogComponent implements OnInit {
    isAddMode: boolean = true;

    form = new FormGroup({
        name: new FormControl<string>('', {
            validators: [Validators.required],
            nonNullable: true
        }),
        content: new FormControl<string>('', {
            validators: [Validators.required],
            nonNullable: true
        }),
    });

    constructor(
        private dialogRef: MatDialogRef<ServiceHeaderFormDialogComponent>,
        @Optional() @Inject(MAT_DIALOG_DATA) public data?: Header
    ) {}

    ngOnInit(): void {
        if (this.data && (this.data.name || this.data.content)) {
            this.isAddMode = false;
            this.form.patchValue({
                name: this.data.name || '',
                content: this.data.content || '',
            });
        }
    }

    onCancel() {
        this.dialogRef.close();
    }

    onSubmit() {
        if (this.form.invalid) {
            this.form.markAllAsTouched();
            return;
        }
        const data = this.form.value as Header;
        this.dialogRef.close(data);
    }

    get f(): { [key: string]: AbstractControl } {
        return this.form.controls;
    }
}
