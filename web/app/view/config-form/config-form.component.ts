import {Component, OnInit} from '@angular/core';
import {Router, RouterModule} from '@angular/router';
import {AbstractControl, FormControl, FormGroup, ReactiveFormsModule} from '@angular/forms';
import {MatTableModule} from '@angular/material/table';
import {ConfigService} from 'app/services/config.service';
import {NotificationService} from 'app/services/notification.service';
import {CommonModule} from '@angular/common';
import {MatMomentDateModule} from '@angular/material-moment-adapter';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatChipsModule} from '@angular/material/chips';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatIconModule} from '@angular/material/icon';
import {MatInputModule} from '@angular/material/input';
import {MatListModule} from '@angular/material/list';
import {MatMenuModule} from '@angular/material/menu';
import {MatPaginatorModule} from '@angular/material/paginator';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {MatSelectModule} from '@angular/material/select';
import {MatSidenavModule} from '@angular/material/sidenav';
import {MatSortModule} from '@angular/material/sort';
import {MatTooltipModule} from '@angular/material/tooltip';
import {TranslatePipe} from '@ngx-translate/core';
import {MatSlideToggleModule} from '@angular/material/slide-toggle';
import {Config} from 'app/models/config';
import {MatTabsModule} from '@angular/material/tabs';
import {MatExpansionModule} from '@angular/material/expansion';
import {OAuthService} from "../../services/oauth.service";

import {TextFieldModule} from '@angular/cdk/text-field';

@Component({
    selector: 'app-config-form',
    standalone: true,
    imports: [
        RouterModule, CommonModule,
        ReactiveFormsModule, TranslatePipe,
        MatMomentDateModule,
        MatSidenavModule, MatIconModule, MatButtonModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule, MatSlideToggleModule,
        MatFormFieldModule, MatChipsModule, MatTabsModule, MatExpansionModule,
        TextFieldModule
    ],
    templateUrl: './config-form.component.html',
    styleUrl: './config-form.component.css'
})
export class ConfigFormComponent implements OnInit {
    submitted = false;
    form = new FormGroup({
        _id: new FormControl<string>(''),
        ca_certificate: new FormControl<string>(''),
        ca_private: new FormControl<string>(''),
        acme_directory_url: new FormControl<string>(''),
        dns_resolver: new FormControl<string>(''),
        archive: new FormGroup({
            enabled: new FormControl<boolean>(false),
            archive_after: new FormControl<number>(1800),
            type: new FormControl<string>('opensearch'),
            url: new FormControl<string>(''),
            username: new FormControl<string>(''),
            password: new FormControl<string>(''),
        }),
        purge: new FormGroup({
            enabled: new FormControl<boolean>(false),
            purge_after: new FormControl<number>(1800)
        }),
        ipxa: new FormGroup({
            url: new FormControl<string>(''),
            key: new FormControl<string>('')
        }),
        telemetry: new FormGroup({
            enabled: new FormControl<boolean>(false),
            url: new FormControl<string>('')
        })
    });

    constructor(
        private notificationService: NotificationService,
        private router: Router,
        private configService: ConfigService,
        protected oauth: OAuthService,
    ) {
    }

    ngOnInit(): void {
        // Fetch active configuration and patch form values
        this.configService.getActive().subscribe(data => {
            const c = (data as any)?.config || data;
            this.form.patchValue({
                _id: c._id,
                ca_certificate: c.ca_certificate,
                ca_private: c.ca_private,
                acme_directory_url: c.acme_directory_url,
                dns_resolver: c.dns_resolver,
                archive: c.archive || {},
                purge: c.purge || {},
                ipxa: c.ipxa || {}
            });
        });
    }

    onSubmit() {
        this.submitted = true;
        if (this.form.status === "INVALID") {
            return;
        }

        const formData = this.form.value as Config;
        this.configService.update(formData._id, formData).subscribe({
            next: (data) => {
                this.notificationService.openSnackBar('Config updated');
                this.router.navigate(['/config']);
            },
            error: (err) => {
                this.notificationService.openSnackBar("Config failed, " + err.message);
            }
        });
    }

    get f(): { [key: string]: AbstractControl } {
        return this.form.controls;
    }
}