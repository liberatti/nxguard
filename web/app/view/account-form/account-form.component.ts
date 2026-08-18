import {Component, OnInit} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators} from '@angular/forms';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatOptionModule} from '@angular/material/core';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatGridListModule} from '@angular/material/grid-list';
import {MatIconModule} from '@angular/material/icon';
import {MatInputModule} from '@angular/material/input';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {MatSelectModule} from '@angular/material/select';
import {MatTooltipModule} from '@angular/material/tooltip';
import {MatChipsModule} from '@angular/material/chips';
import {RouterModule} from '@angular/router';
import {TranslatePipe, TranslateService} from '@ngx-translate/core';
import {User} from 'app/models/oauth';
import {OAuthService, UserService} from 'app/services/oauth.service';
import {MatTabsModule} from "@angular/material/tabs";
import {NotificationService} from "../../services/notification.service";

@Component({
    selector: 'app-account-form',
    standalone: true,
    imports: [
        CommonModule,
        RouterModule,
        FormsModule,
        ReactiveFormsModule,
        TranslatePipe,
        MatIconModule,
        MatButtonModule,
        MatFormFieldModule,
        MatCardModule,
        MatProgressBarModule,
        MatInputModule,
        MatTooltipModule,
        MatSelectModule,
        MatOptionModule,
        MatGridListModule,
        MatChipsModule,
        MatTabsModule,
    ],
    templateUrl: './account-form.component.html',
    styleUrl: './account-form.component.css'
})
export class AccountComponent implements OnInit {
    userInfo: any = {} as any;
    hidePassword = true;

    form = new FormGroup({
        _id: new FormControl<string>('', {
            validators: [Validators.required],
        }),
        name: new FormControl<string>('', {
            validators: [Validators.required],
        }),
        email: new FormControl<string>('', {
            validators: [Validators.required, Validators.email],
        }),
        password: new FormControl<string>(''),
    });

    constructor(
        private userService: UserService,
        private authService: OAuthService,
        private notificationService: NotificationService,
        private translate: TranslateService
    ) {}

    ngOnInit() {
        this.userInfo = this.authService.userInfo();
        if (this.userInfo && this.userInfo._id) {
            this.userService.getById(this.userInfo._id).subscribe(data => {
                if (data) {
                    this.form.get('_id')?.setValue(data._id);
                    this.form.get('email')?.setValue(data.email);
                    this.form.get('name')?.setValue(data.name);
                }
            });
        }
    }

    onSubmit() {
        if (this.form.invalid) {
            return;
        }

        const formData = { ...this.form.value } as any;
        if (!formData.password) {
            delete formData.password;
        }

        this.userService.updateAccount(formData._id, formData).subscribe(() => {
            this.notificationService.openSnackBar(this.translate.instant('ACCOUNT.SUCCESS'));
        });
    }
}
