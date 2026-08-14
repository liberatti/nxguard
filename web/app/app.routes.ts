import {Routes} from '@angular/router';
import {AdminLayoutComponent} from './layouts/admin-layout/admin-layout.component';
import {SignInComponent} from './view/sign-in/sign-in.component';
import {PublicLayoutComponent} from './layouts/public-layout/public-layout.component';
import {CertificateListComponent} from './view/certificate-list/certificate-list.component';
import {CertificateFormComponent} from './view/certificate-form/certificate-form.component';
import {UpstreamListComponent} from './view/upstream-list/upstream-list.component';
import {UpstreamFormComponent} from './view/upstream-form/upstream-form.component';
import {SensorListComponent} from './view/sensor-list/sensor-list.component';
import {SensorFormComponent} from './view/sensor-form/sensor-form.component';
import {ServiceListComponent} from './view/service-list/service-list.component';
import {ServiceFormComponent} from './view/service-form/service-form.component';
import {AccountComponent} from './view/account-form/account-form.component';
import {TransactionListComponent} from './view/transaction-list/transaction-list.component';
import {ConfigFormComponent} from './view/config-form/config-form.component';
import {DashboardHomeComponent} from "./view/dashboard-home/dashboard-home.component";
import {UserListComponent} from "./view/user-list/user-list.component";
import {UserFormComponent} from "./view/user-form/user-form.component";

export const routes: Routes = [
    {
        path: 'signin',
        component: PublicLayoutComponent,
        children: [
            {path: '', component: SignInComponent},
        ]
    },
    {
        path: '',
        component: AdminLayoutComponent,
        children: [
            {path: '', redirectTo: 'dashboard', pathMatch: 'full'},
            {path: 'dashboard', component: DashboardHomeComponent},
            {path: 'trn', component: TransactionListComponent},
            {
                path: 'service',
                children: [
                    {path: '', component: ServiceListComponent},
                    {path: 'add', component: ServiceFormComponent},
                    {path: 'edit/:id', component: ServiceFormComponent},
                ]
            },
            {
                path: 'users',
                children: [
                    {path: '', component: UserListComponent},
                    {path: 'add', component: UserFormComponent},
                    {path: 'edit/:id', component: UserFormComponent},
                ]
            },
            {
                path: 'ups',
                children: [
                    {path: '', component: UpstreamListComponent},
                    {path: 'add', component: UpstreamFormComponent},
                    {path: 'edit/:id', component: UpstreamFormComponent},
                ]
            },
            {
                path: 'sensor',
                children: [
                    {path: '', component: SensorListComponent},
                    {path: 'add', component: SensorFormComponent},
                    {path: 'edit/:id', component: SensorFormComponent},
                ]
            },
            {
                path: 'certificate',
                children: [
                    {path: '', component: CertificateListComponent},
                    {path: 'add', component: CertificateFormComponent},
                    {path: 'edit/:id', component: CertificateFormComponent},
                ]
            },
            {path: 'account', component: AccountComponent},
            {path: 'config', component: ConfigFormComponent},
        ]
    },
    {
        path: '**',
        redirectTo: 'dashboard',
        pathMatch: 'full'
    }
];