import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { AbstractControl, FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatDialog } from '@angular/material/dialog';
import { CommonModule } from '@angular/common';
import { MatMomentDateModule } from '@angular/material-moment-adapter';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule } from '@angular/material/menu';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSortModule } from '@angular/material/sort';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { TranslatePipe } from '@ngx-translate/core';
import {
    ServiceBindFormDialogComponent
} from 'app/components/service-bind-form-dialog/service-bind-form-dialog.component';
import {
    ServiceHeaderFormDialogComponent
} from 'app/components/service-header-form-dialog/service-header-form-dialog.component';
import {
    ServiceRouteFormDialogComponent
} from 'app/components/service-route-form-dialog/service-route-form-dialog.component';
import { Upstream } from 'app/models/upstream';
import { Sensor } from 'app/models/sensor';
import { Bind, Header, ProtocolType, Route, Service } from 'app/models/service';
import { ServiceService } from 'app/services/service.service';
import { NotificationService } from 'app/services/notification.service';
import { DragDropModule } from '@angular/cdk/drag-drop';
import { MatExpansionModule } from '@angular/material/expansion';
import { Certificate } from "../../models/certificate";
import { CertificateService } from "../../services/certificate.service";
import { MatStepper, MatStepperModule } from "@angular/material/stepper";
import { OAuthService } from "../../services/oauth.service";
import { minArrayLength } from '../../validators/min-array-length.validator';
import { RouteService } from 'app/services/route.service';

@Component({
    selector: 'app-service-form',
    standalone: true,
    imports: [RouterModule, CommonModule, MatExpansionModule,
        ReactiveFormsModule, TranslatePipe,
        MatMomentDateModule, DragDropModule,
        MatSidenavModule, MatIconModule, MatButtonModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule, MatTabsModule, MatGridListModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule, MatSlideToggleModule, MatCheckboxModule,
        MatFormFieldModule, MatChipsModule, MatStepperModule],
    templateUrl: './service-form.component.html',
    styleUrls: ['./service-form.component.css']
})
export class ServiceFormComponent implements OnInit {

    _certificates: Certificate[];
    basicHeaders = [
        <Header>{ name: "X-Powered-By", content: "NXGuard" },
        <Header>{ name: "X-XSS-Protection", content: "1; mode=block" },
        <Header>{ name: "X-Frame-Options", content: "SAMEORIGIN" }
    ];
    isAddMode: boolean;
    bindingDS: MatTableDataSource<Bind>;
    bindingDC: string[] = ['port', 'protocol', 'ssl_upgrade', 'action'];

    headerDS: MatTableDataSource<Header>;
    headerDC: string[] = ['name', 'content', 'action'];

    routeDS: MatTableDataSource<Route>;
    routeDC: string[] = ['Name', 'Upstream Target', 'Location Paths', 'action'];

    sansForm = new FormGroup({
        cn: new FormControl<string>('')
    });

    compressionForm = new FormGroup({
        type: new FormControl<string>('')
    });

    protocolForm = new FormGroup({
        text: new FormControl<string>('')
    });

    form = new FormGroup({
        _id: new FormControl<string>(""),
        name: new FormControl<string>('', {
            validators: [
                Validators.required,
                Validators.minLength(4),
            ]
        }),
        body_limit: new FormControl<number>(10),
        timeout: new FormControl<number>(120),
        bindings: new FormControl<Array<Bind>>([] as Array<Bind>, {
            validators: [
                Validators.required,
                minArrayLength(1)
            ]
        }),
        headers: new FormControl<Array<Header>>([]),
        routes: new FormControl<Array<Route>>([]),
        inspect_level: new FormControl<number>(3),
        inbound_score: new FormControl<number>(15),
        outbound_score: new FormControl<number>(15),
        buffer: new FormControl<number>(256),
        compression_types: new FormControl<Array<string>>([
            'text/plain',
            'text/html',
            'text/css',
            'application/json',
            'application/xml',
            'application/javascript',
            'text/xml',
            'application/xml+rss',
            'text/javascript'
        ]),
        rate_limit_per_sec: new FormControl<number>(256),
        sans: new FormControl<Array<string>>([], [Validators.required, minArrayLength(1)]),
        ssl_protocols: new FormControl<Array<string>>(['TLSv1', 'TLSv1.1', 'TLSv1.2', 'TLSv1.3']),
        certificate: new FormControl<Certificate>({} as Certificate),

        ssl_client_auth: new FormControl<boolean>(false),
        ssl_client_ca: new FormControl<string>(''),
    });

    constructor(
        private route: ActivatedRoute,
        private router: Router,
        private confirmDialog: MatDialog,
        private notificationService: NotificationService,
        private serviceService: ServiceService,
        private routeService: RouteService,
        private certificateService: CertificateService,
        protected oauth: OAuthService,
    ) {
        this.headerDS = new MatTableDataSource<Header>;
        this.routeDS = new MatTableDataSource<Route>;
        this.bindingDS = new MatTableDataSource<Bind>;
        this.isAddMode = false;
        this._certificates = [];
    }

    ngOnInit(): void {
        // Extract id from route params
        const { id } = this.route.snapshot.params;
        this.isAddMode = !id;

        this.certificateService.get().subscribe(certData => {
            this._certificates = certData.data;

            if (!this.isAddMode) {
                this.serviceService.getById(id).subscribe(data => {
                    this.form.patchValue({
                        _id: data._id as string,
                        name: data.name,
                        headers: data.headers,
                        bindings: data.bindings,
                        body_limit: data.body_limit,
                        timeout: data.timeout,
                        buffer: data.buffer,
                        sans: data.sans,
                        compression_types: data.compression_types,
                        rate_limit_per_sec: data.rate_limit_per_sec,
                        certificate: data.certificate,
                        ssl_protocols: data.ssl_protocols,
                        ssl_client_auth: data.ssl_client_auth,
                        ssl_client_ca: data.ssl_client_auth ? data.ssl_client_ca : ''
                    });

                    // Update data sources
                    this.headerDS.data = data.headers;
                    this.bindingDS.data = data.bindings;

                    this.routeService.getByServiceId(id).subscribe((routeRes: any) => {
                        const routes = routeRes.data || routeRes || [];
                        this.form.patchValue({ routes: routes });
                        this.routeDS.data = routes;
                    });
                });
            } else {
                this.form.get('headers')?.setValue(this.basicHeaders);
                this.headerDS.data = this.basicHeaders;
                this.form.get('bindings')?.setValue([{ 'port': 80, 'protocol': ProtocolType.HTTP, 'ssl_upgrade': false }] as Array<Bind>);
                this.bindingDS.data = this.form.get('bindings')?.value as Array<Bind>;
            }
        });
    }

    hasSslSupport() {
        if (this.form.value.bindings)
            for (const binding of this.form.value.bindings) {
                if (binding.protocol == 'HTTPS') {
                    return true;
                }
            }
        return false;
    }

    onAddCN(): void {
        const formData = this.sansForm.value.cn as string;
        const currentSans = this.form.get('sans')?.value || [];
        this.form.get('sans')?.setValue([...currentSans, formData]);
        this.sansForm.reset();
    }

    onRemoveCN(keyword: any): void {
        const currentSans = this.form.get('sans')?.value || [];
        this.form.get('sans')?.setValue(currentSans.filter((item: string) => item !== keyword));
    }

    moveRoute(event: any) {
        const _data = this.form.value as Service;
        let element = _data.routes[event.previousIndex];
        _data.routes.splice(event.previousIndex, 1);
        _data.routes.splice(event.currentIndex, 0, element);
        this.form.reset(_data);
    }

    onNextDetails(stepper: MatStepper) {
        if (!this.form.get('name')?.valid || !this.form.get('sans')?.valid || !this.form.get('bindings')?.valid) {
            let errors = [] as Array<string>;
            if (!this.form.get('name')?.valid) errors.push(' Invalid value on name');
            if (!this.form.get('sans')?.valid) errors.push(' Invalid value on sans');
            if (!this.form.get('bindings')?.valid) errors.push(' Invalid value on bindings');
            this.notificationService.openSnackBar(errors);
            return;
        }

        let _data: Service = JSON.parse(JSON.stringify(this.form.value));

        if (_data._id === "") {
            Reflect.deleteProperty(_data, '_id');
        }

        if (!this.hasSslSupport()) {
            Reflect.deleteProperty(_data, 'certificate');
        } else {
            _data.certificate = { "_id": _data.certificate._id } as Certificate;
        }

        if (this.isAddMode) {
            this.serviceService.save(_data).subscribe((res: any) => {
                const created = res.data || res;
                if (created && created._id) {
                    this.form.patchValue({ _id: String(created._id) });
                    this.isAddMode = false;
                    this.notificationService.openSnackBar('Service saved');
                }
                stepper.next();
            });
        } else {
            this.serviceService.update(_data._id as string, _data).subscribe(() => {
                this.notificationService.openSnackBar('Service updated');
                stepper.next();
            });
        }
    }

    onSubmit() {
        if (this.form.status === "INVALID") {
            let errors = [] as Array<string>;
            Object.keys(this.form.controls)
                .forEach(k => {
                    let control = this.form.get(k) as FormControl;
                    if (control.status !== "VALID") {
                        errors.push(" Invalid value on " + k);
                    }
                });

            if (errors.length > 0) {
                console.log(this.form.value);
                this.notificationService.openSnackBar(errors);
            }
            return;
        }
        let _data: Service = JSON.parse(JSON.stringify(this.form.value));

        if (_data._id === "") {
            Reflect.deleteProperty(_data, '_id');
        }

        if (!this.hasSslSupport()) {
            Reflect.deleteProperty(_data, 'certificate');
        } else {
            _data.certificate = { "_id": _data.certificate._id } as Certificate;
        }

        if (this.isAddMode) {
            this.serviceService.save(_data).subscribe((data) => {
                this.router.navigate(['/service']);
                this.notificationService.openSnackBar('Service saved');
            });
        } else {
            this.serviceService.update(_data._id as string, _data).subscribe((data) => {
                this.router.navigate(['/service']);
                this.notificationService.openSnackBar('Service updated');
            });
        }
    }

    onBindRemove(index: number) {
        const data = this.bindingDS.data;
        data.splice(index, 1);
        this.bindingDS.data = data;
    }

    onAddBind() {
        let excludeList = [] as Array<string>;
        for (const b of this.bindingDS.data) {
            excludeList.push(b.protocol);
        }
        const dialogRef = this.confirmDialog.open(ServiceBindFormDialogComponent, {
            width: '450px',
            data: {
                bind: {} as Bind,
                supportedProtocols: ['HTTP', 'HTTPS'].filter(item => !excludeList.includes(item)) as Array<string>
            }
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                const data = this.bindingDS.data;
                data.push(result);
                this.bindingDS.data = data;
                this.form.get('bindings')?.setValue(data);
            }
        });
    }

    onEditBind(index: number) {
        const dialogRef = this.confirmDialog.open(ServiceBindFormDialogComponent,
            {
                maxWidth: undefined,
                data: this.bindingDS.data[index]
            });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                this.onBindRemove(index);
                const data = this.bindingDS.data;
                data.push(result);
                this.bindingDS.data = data;
                this.form.get('bindings')?.setValue(data);
            }
        });
    }

    onRemoveHeader(selectedIndex: number) {
        const data = this.headerDS.data;
        data.splice(selectedIndex, 1);
        this.headerDS.data = data;
    }

    onAddHeader() {
        const dialogRef = this.confirmDialog.open(ServiceHeaderFormDialogComponent, {
            width: '450px',
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                const data = this.headerDS.data;
                data.push(result);
                this.headerDS.data = data;
                this.form.get('headers')?.reset(data);
            }
        });
    }

    onRemoveRoute(index: number) {
        const targetRoute = this.routeDS.data[index];
        const serviceId = this.form.get('_id')?.value;
        if (targetRoute && targetRoute._id) {
            this.routeService.removeById(targetRoute._id).subscribe(() => {
                if (serviceId) {
                    this.routeService.getByServiceId(serviceId).subscribe((res: any) => {
                        const routes = res.data || res || [];
                        this.form.get('routes')?.setValue(routes);
                        this.routeDS.data = routes;
                    });
                }
            });
        } else {
            const currentRoutes = this.form.get('routes')?.value || [];
            const newRoutes = currentRoutes.slice();
            newRoutes.splice(index, 1);
            this.form.get('routes')?.setValue(newRoutes);
            this.routeDS.data = newRoutes;
        }
    }

    onAddRoute() {
        const dialogRef = this.confirmDialog.open(ServiceRouteFormDialogComponent,
            {
                maxWidth: undefined
            });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                const serviceId = this.form.get('_id')?.value;
                if (serviceId) {
                    result.service_id = serviceId;
                    if (result.upstream && result.upstream._id) {
                        result.upstream = <Upstream>{ _id: result.upstream._id };
                    }
                    if (result.sensor && result.sensor._id) {
                        result.sensor = <Sensor>{ _id: result.sensor._id };
                    } else {
                        Reflect.deleteProperty(result, 'sensor');
                    }
                    this.routeService.save(result).subscribe(() => {
                        this.routeService.getByServiceId(serviceId).subscribe((res: any) => {
                            const routes = res.data || res || [];
                            this.form.get('routes')?.setValue(routes);
                            this.routeDS.data = routes;
                        });
                    });
                } else {
                    const currentRoutes = this.form.get('routes')?.value || [];
                    this.form.get('routes')?.setValue([...currentRoutes, result]);
                    this.routeDS.data = this.form.get('routes')?.value || [];
                }
            }
        });
    }

    onEditRoute(index: number) {
        const targetRoute = this.routeDS.data[index];
        const dialogRef = this.confirmDialog.open(ServiceRouteFormDialogComponent,
            {
                maxWidth: undefined,
                data: targetRoute
            });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                const serviceId = this.form.get('_id')?.value;
                if (serviceId) {
                    result.service_id = serviceId;
                    if (result.upstream && result.upstream._id) {
                        result.upstream = <Upstream>{ _id: result.upstream._id };
                    }
                    if (result.sensor && result.sensor._id) {
                        result.sensor = <Sensor>{ _id: result.sensor._id };
                    } else {
                        Reflect.deleteProperty(result, 'sensor');
                    }

                    if (targetRoute && targetRoute._id) {
                        result._id = targetRoute._id;
                        this.routeService.update(String(targetRoute._id), result).subscribe(() => {
                            this.routeService.getByServiceId(serviceId).subscribe((res: any) => {
                                const routes = res.data || res || [];
                                this.form.get('routes')?.setValue(routes);
                                this.routeDS.data = routes;
                            });
                        });
                    } else {
                        this.routeService.save(result).subscribe(() => {
                            this.routeService.getByServiceId(serviceId).subscribe((res: any) => {
                                const routes = res.data || res || [];
                                this.form.get('routes')?.setValue(routes);
                                this.routeDS.data = routes;
                            });
                        });
                    }
                } else {
                    const currentRoutes = this.form.get('routes')?.value || [];
                    const newRoutes = currentRoutes.slice();
                    newRoutes[index] = result;
                    this.form.get('routes')?.setValue(newRoutes);
                    this.routeDS.data = newRoutes;
                }
            }
        });
    }

    onAddProto(): void {
        let data = this.protocolForm.value.text as string;
        const currentProtocols = this.form.get('ssl_protocols')?.value || [];
        this.form.get('ssl_protocols')?.setValue([...currentProtocols, data]);
        console.log(this.form.get('ssl_protocols')?.value);
        this.protocolForm.reset();
    }

    onRemoveProto(keyword: any): void {
        if (this.form.enabled)
            if (this.form.value.ssl_protocols != null) {
                let index = this.form.value.ssl_protocols.indexOf(keyword);
                if (index >= 0) {
                    this.form.value.ssl_protocols.splice(index, 1);
                }
            }
    }

    onAddCompressionType(): void {
        const formData = this.compressionForm.value.type as string;
        const currentTypes = this.form.get('compression_types')?.value || [];
        this.form.get('compression_types')?.setValue([...currentTypes, formData]);
        this.compressionForm.reset();
    }

    onRemoveCompressionType(keyword: any): void {
        if (this.form.value.compression_types != null) {
            let index = this.form.value.compression_types.indexOf(keyword);
            if (index >= 0) {
                this.form.value.compression_types.splice(index, 1);
            }
        }
    }

    compareFn(object1: any, object2: any) {
        if (!object1 || !object2) return false;
        if (object1._id != null && object2._id != null) {
            return String(object1._id) === String(object2._id);
        }
        if (object1.name && object2.name) {
            return object1.name === object2.name;
        }
        return object1 === object2;
    }

    get f(): { [key: string]: AbstractControl } {
        return this.form.controls;
    }
}