import { Component, Inject, OnInit } from '@angular/core';
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
import { Bind, ProtocolType } from 'app/models/service';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatTooltipModule } from '@angular/material/tooltip';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
    selector: 'app-service-bind-form-dialog',
    templateUrl: './service-bind-form-dialog.component.html',
    styleUrl: './service-bind-form-dialog.component.css',
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
        MatSelectModule,
        MatSlideToggleModule,
        MatTooltipModule,
        TranslatePipe,
    ],
})
export class ServiceBindFormDialogComponent implements OnInit {
    isAddMode: boolean = true;
    _supportedProtocols = ['HTTP', 'HTTPS'];

    form = new FormGroup({
        port: new FormControl<number>(80, {
            validators: [Validators.required, Validators.min(1), Validators.max(65535)],
        }),
        protocol: new FormControl<ProtocolType>(ProtocolType.HTTP, {
            validators: [Validators.required],
        }),
        ssl_upgrade: new FormControl<boolean>(false),
        ssl_upgrade_port: new FormControl<number>(443, {
            validators: [Validators.min(1), Validators.max(65535)],
        }),
    });

    constructor(
        private dialogRef: MatDialogRef<ServiceBindFormDialogComponent>,
        @Inject(MAT_DIALOG_DATA) public bindData: any,
    ) {}

    ngOnInit(): void {
        if (this.bindData) {
            if ('supportedProtocols' in this.bindData) {
                this.isAddMode = true;
                if (this.bindData.supportedProtocols && this.bindData.supportedProtocols.length > 0) {
                    this._supportedProtocols = this.bindData.supportedProtocols;
                }
                const b = this.bindData.bind as Bind;
                if (b && b.protocol) {
                    this.form.get('protocol')?.setValue(b.protocol);
                    if (b.port != null) this.form.get('port')?.setValue(b.port);
                    this.form.get('ssl_upgrade')?.setValue(!!b.ssl_upgrade);
                    this.form.get('ssl_upgrade_port')?.setValue(b.ssl_upgrade_port ?? 443);
                } else if (this._supportedProtocols.length > 0) {
                    const defaultProto = this._supportedProtocols[0] as ProtocolType;
                    this.form.get('protocol')?.setValue(defaultProto);
                    this.form.get('port')?.setValue(defaultProto === 'HTTPS' ? 443 : 80);
                }
            } else {
                const b = this.bindData as Bind;
                this.isAddMode = !(b && (b.protocol || b.port != null));
                if (b.port != null) this.form.get('port')?.setValue(b.port);
                if (b.protocol) this.form.get('protocol')?.setValue(b.protocol);
                this.form.get('ssl_upgrade')?.setValue(!!b.ssl_upgrade);
                this.form.get('ssl_upgrade_port')?.setValue(b.ssl_upgrade_port ?? 443);
            }
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
        let data = this.form.value as Bind;
        data.ssl_upgrade = !!data.ssl_upgrade;
        data.ssl_upgrade_port = data.ssl_upgrade_port ?? 443;

        this.dialogRef.close(data);
    }

    get f(): { [key: string]: AbstractControl } {
        return this.form.controls;
    }
}
