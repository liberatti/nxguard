import { Component, Inject, OnInit, ViewChild } from '@angular/core';
import {
    MAT_DIALOG_DATA,
    MatDialogActions,
    MatDialogContent,
    MatDialogRef,
    MatDialogTitle
} from '@angular/material/dialog';
import { AbstractControl, FormControl, FormGroup, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { COMMA, ENTER } from '@angular/cdk/keycodes';
import { Sensor } from 'app/models/sensor';
import { Route, RouteType } from 'app/models/service';
import { Upstream } from 'app/models/upstream';
import { UpstreamService } from 'app/services/upstream.service';
import { SensorService } from 'app/services/sensor.service';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatChipsModule } from '@angular/material/chips';
import { MatSlideToggle } from '@angular/material/slide-toggle';
import { MatTabGroup, MatTabsModule } from '@angular/material/tabs';
import { TranslatePipe } from '@ngx-translate/core';
import { StaticServer } from "../../models/static";
import { StaticService } from "../../services/static.service";


@Component({
    selector: 'app-service-route-form-dialog',
    templateUrl: './service-route-form-dialog.component.html',
    standalone: true,
    imports: [ReactiveFormsModule, CommonModule, TranslatePipe,
        MatFormFieldModule, MatChipsModule,
        MatInputModule,
        FormsModule, MatCardModule,
        MatButtonModule,
        MatDialogTitle,
        MatDialogContent,
        MatDialogActions, MatSlideToggle,
        MatIconModule, MatSelectModule, MatTabsModule
    ],
})

export class ServiceRouteFormDialogComponent implements OnInit {
    @ViewChild('tabGroup') tabGroup!: MatTabGroup;
    _supportedTypes: RouteType[] = [RouteType.UPSTREAM, RouteType.REDIRECT];
    _allowed_methods: string[] = [
        'GET', 'HEAD', 'POST', 'OPTIONS', 'PUT', 'PATCH', 'DELETE'
    ];
    _allowed_content_type: string[] = [
        'application/x-www-form-urlencoded',
        'multipart/form-data',
        'text/xml',
        'application/xml',
        'application/soap+xml',
        'application/json'
    ];
    separatorKeysCodes = [COMMA, ENTER];
    _upstreams: Upstream[] = [];
    _sensors: Sensor[] = [];
    isAddMode: boolean;
    submitted = false;

    pathForm = new FormGroup({
        path: new FormControl<string>('')
    });

    methodForm = new FormGroup({
        method: new FormControl<string>('')
    });
    allowedMethodForm = new FormGroup({
        allowedMethod: new FormControl<string>('')
    });
    allowedContentTypeForm = new FormGroup({
        allowedContentType: new FormControl<string>('')
    });
    cacheMethodForm = new FormGroup({
        cacheMethod: new FormControl<string>('')
    });

    form = new FormGroup({
        name: new FormControl<string>(""),
        upstream: new FormControl<Upstream>(<Upstream>{}),
        static: new FormControl<StaticServer>(<StaticServer>{}),
        redirect: new FormGroup({
            code: new FormControl<number>(500),
            url: new FormControl<string>('')
        }),
        paths: new FormControl<Array<string>>([]),
        methods: new FormControl<Array<string>>(['GET', 'POST', 'PUT', 'PATCH', 'DELETE']),
        allowed_methods: new FormControl<Array<string> | string>(['GET', 'HEAD', 'POST', 'OPTIONS', 'PUT', 'PATCH', 'DELETE']),
        allowed_content_type: new FormControl<Array<string> | string>([
            'application/x-www-form-urlencoded',
            'multipart/form-data',
            'text/xml',
            'application/xml',
            'application/soap+xml',
            'application/json'
        ]),
        monitor_only: new FormControl<boolean>(false),
        sensor: new FormControl<Sensor>(<Sensor>{}),
        cache_methods: new FormControl<Array<string>>([]),
        type: new FormControl<RouteType>(RouteType.UPSTREAM),
    });

    constructor(
        private dialogRef: MatDialogRef<any>,
        private upstreamService: UpstreamService,
        private staticService: StaticService,
        private sensorService: SensorService,
        @Inject(MAT_DIALOG_DATA) public routeData: Route
    ) {
        this.isAddMode = false;
    }

    ngOnInit(): void {
        this.upstreamService.get().subscribe(data => {
            this._upstreams = data.data;
        });

        this.sensorService.get().subscribe(data => {
            this._sensors = data.data;
            if (this.isAddMode) {
                this.form.get('sensor')?.setValue(this._sensors[0]);
            }
        });
        this.isAddMode = !this.routeData;
        if (!this.isAddMode) {
            this.form.patchValue({
                name: this.routeData.name,
                upstream: this.routeData.upstream,
                static: this.routeData.static,
                redirect: this.routeData.redirect,
                paths: this.routeData.paths,
                methods: this.routeData.methods,
                allowed_methods: this.routeData.allowed_methods || ['GET', 'HEAD', 'POST', 'OPTIONS', 'PUT', 'PATCH', 'DELETE'],
                allowed_content_type: this.routeData.allowed_content_type || [
                    'application/x-www-form-urlencoded',
                    'multipart/form-data',
                    'text/xml',
                    'application/xml',
                    'application/soap+xml',
                    'application/json'
                ],
                monitor_only: this.routeData.monitor_only,
                sensor: this.routeData.sensor,
                type: this.routeData.type,
                cache_methods: this.routeData.cache_methods || []
            });
        }
    }

    onCancel() {
        this.dialogRef.close();
    }

    onSubmit() {
        if (this.form.status === "INVALID") {
            return;
        }
        let data = this.form.value as Route;
        this.dialogRef.close(data);
    }

    onAddPath(): void {
        let data = this.pathForm.value.path as string;
        this.form.value.paths?.push(data);
        this.pathForm.reset();
    }

    onRemovePath(keyword: any): void {
        if (this.form.value.paths != null) {
            let index = this.form.value.paths.indexOf(keyword);
            if (index >= 0) {
                this.form.value.paths.splice(index, 1);
            }
        }
    }

    onAddMethod(): void {
        let data = this.methodForm.value.method as string;
        this.form.value.methods?.push(data);
        this.methodForm.reset();
    }

    onRemoveMethod(keyword: any): void {
        if (this.form.value.methods != null) {
            let index = this.form.value.methods.indexOf(keyword);
            if (index >= 0) {
                this.form.value.methods.splice(index, 1);
            }
        }
    }

    onAddCacheMethod(): void {
        let data = this.cacheMethodForm.value.cacheMethod as string;
        this.form.value.cache_methods?.push(data);
        this.cacheMethodForm.reset();
    }

    onRemoveCacheMethod(keyword: any): void {
        if (this.form.value.cache_methods != null) {
            let index = this.form.value.cache_methods.indexOf(keyword);
            if (index >= 0) {
                this.form.value.cache_methods.splice(index, 1);
            }
        }
    }

    onAddAllowedMethod(): void {
        let data = this.allowedMethodForm.value.allowedMethod as string;
        if (!data) return;
        let current = this.getArrayVal(this.form.value.allowed_methods);
        if (!current.includes(data)) {
            current.push(data);
            this.form.get('allowed_methods')?.setValue(current);
        }
        this.allowedMethodForm.reset();
    }

    onRemoveAllowedMethod(keyword: any): void {
        let current = this.getArrayVal(this.form.value.allowed_methods);
        let index = current.indexOf(keyword);
        if (index >= 0) {
            current.splice(index, 1);
            this.form.get('allowed_methods')?.setValue(current);
        }
    }

    filterActiveAllowedMethod(list: string[]): string[] {
        const selected = this.getArrayVal(this.form.value.allowed_methods);
        return list.filter(item => !selected.includes(item));
    }

    onAddAllowedContentType(): void {
        let data = this.allowedContentTypeForm.value.allowedContentType as string;
        if (!data) return;
        let current = this.getArrayVal(this.form.value.allowed_content_type);
        if (!current.includes(data)) {
            current.push(data);
            this.form.get('allowed_content_type')?.setValue(current);
        }
        this.allowedContentTypeForm.reset();
    }

    onRemoveAllowedContentType(keyword: any): void {
        let current = this.getArrayVal(this.form.value.allowed_content_type);
        let index = current.indexOf(keyword);
        if (index >= 0) {
            current.splice(index, 1);
            this.form.get('allowed_content_type')?.setValue(current);
        }
    }

    filterActiveAllowedContentType(list: string[]): string[] {
        const selected = this.getArrayVal(this.form.value.allowed_content_type);
        return list.filter(item => !selected.includes(item));
    }

    getArrayVal(val: any): string[] {
        if (!val) return [];
        if (typeof val === 'string') return val.split(' ').filter(x => x);
        return [...val];
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