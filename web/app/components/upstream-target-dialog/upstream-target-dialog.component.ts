import { CommonModule } from '@angular/common';
import { Component, Inject, OnInit } from '@angular/core';
import { AbstractControl, FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
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
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatTooltipModule } from '@angular/material/tooltip';
import { TranslatePipe } from '@ngx-translate/core';
import { TargetEntity } from 'app/models/service';

@Component({
    selector: 'app-upstream-target-dialog',
    templateUrl: './upstream-target-dialog.component.html',
    styleUrl: './upstream-target-dialog.component.css',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
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
        TranslatePipe,
    ],
})
export class UpstreamTargetDialogComponent implements OnInit {
    isAddMode: boolean = true;

    form = new FormGroup({
        _id: new FormControl<string>(''),
        host: new FormControl<string>('', {
            validators: [Validators.required],
        }),
        port: new FormControl<number>(80, {
            validators: [Validators.required, Validators.min(1), Validators.max(65535)],
        }),
        weight: new FormControl<number>(100, {
            validators: [Validators.min(1)],
        }),
    });

    constructor(
        private dialogRef: MatDialogRef<UpstreamTargetDialogComponent>,
        @Inject(MAT_DIALOG_DATA) public data: TargetEntity | null
    ) {
        this.isAddMode = !data || !data.host;
    }

    ngOnInit(): void {
        if (this.data) {
            this.form.patchValue(this.data);
        }
    }

    get f(): { [key: string]: AbstractControl } {
        return this.form.controls;
    }

    public cancel() {
        this.dialogRef.close();
    }

    onSubmit() {
        if (this.form.invalid) {
            this.form.markAllAsTouched();
            return;
        }
        this.dialogRef.close(this.form.value as TargetEntity);
    }
}