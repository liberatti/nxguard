import { Component, Inject, OnInit } from '@angular/core';
import {
    MAT_DIALOG_DATA,
    MatDialogActions,
    MatDialogContent,
    MatDialogRef,
    MatDialogTitle
} from '@angular/material/dialog';
import { AbstractControl, FormControl, FormGroup, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { Bind, ProtocolType } from 'app/models/service';
import { MatSelectModule } from '@angular/material/select';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatChipsModule } from '@angular/material/chips';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
    selector: 'app-service-bind-form-dialog',
    templateUrl: './service-bind-form-dialog.component.html',
    standalone: true,
    imports: [ReactiveFormsModule, CommonModule,
        MatFormFieldModule,
        MatInputModule,
        FormsModule, MatCardModule,
        MatButtonModule,
        MatDialogTitle,
        MatDialogContent,
        MatDialogActions,
        MatChipsModule,
        MatIconModule, MatSelectModule, MatCheckboxModule,
        TranslatePipe
    ],
})
export class ServiceBindFormDialogComponent implements OnInit {
    _supportedProtocols = ['HTTP', 'HTTPS'];

    form = new FormGroup({
        port: new FormControl<number>(80),
        protocol: new FormControl<ProtocolType>(ProtocolType.HTTP),
        ssl_upgrade: new FormControl<boolean>(false),
        ssl_upgrade_port: new FormControl<number>(443),

    });

    constructor(
        private dialogRef: MatDialogRef<any>,
        @Inject(MAT_DIALOG_DATA) public bindData: Bind,
    ) {

    }

    ngOnInit(): void {
        if (this.bindData) {
            this.form.get('port')?.setValue(this.bindData.port);
            this.form.get('protocol')?.setValue(this.bindData.protocol);
            this.form.get('ssl_upgrade')?.setValue(this.bindData.ssl_upgrade ?? false);
            this.form.get('ssl_upgrade_port')?.setValue(this.bindData.ssl_upgrade_port ?? 443);
        }
    }

    onCancel() {
        this.dialogRef.close();
    }

    onSubmit() {
        if (this.form.status === "INVALID") {
            return;
        }
        let data = this.form.value as Bind;
        data.ssl_upgrade = !!data.ssl_upgrade;
        data.ssl_upgrade_port = data.ssl_upgrade_port ?? 443;

        this.dialogRef.close(data);
    }

    get f(): { [key: string]: AbstractControl } {
        return this.form.controls;
    }

    compareFn(object1: any, object2: any) {
        return object1 && object2 && object1._id === object2._id;
    }


}