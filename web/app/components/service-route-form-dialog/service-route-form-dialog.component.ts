import {Component, Inject, OnInit, ViewChild} from '@angular/core';
import {
    MAT_DIALOG_DATA,
    MatDialogActions,
    MatDialogContent,
    MatDialogRef,
    MatDialogTitle
} from '@angular/material/dialog';
import {AbstractControl, FormControl, FormGroup, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {COMMA, ENTER} from '@angular/cdk/keycodes';
import {Sensor} from 'app/models/sensor';
import {Route, RouteFilter} from 'app/models/service';
import {Upstream} from 'app/models/upstream';
import {UpstreamService} from 'app/services/upstream.service';
import {SensorService} from 'app/services/sensor.service';
import {CommonModule} from '@angular/common';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatIconModule} from '@angular/material/icon';
import {MatInputModule} from '@angular/material/input';
import {MatSelectModule} from '@angular/material/select';
import {MatChipsModule} from '@angular/material/chips';
import {MatSlideToggle} from '@angular/material/slide-toggle';
import {MatTabGroup, MatTabsModule} from '@angular/material/tabs';
import {TranslatePipe} from '@ngx-translate/core';
import {StaticServer} from "../../models/static";
import {StaticService} from "../../services/static.service";
import {RoutefilterService} from "../../services/routefilter.service";


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
    _supportedTypes: string[] = ['upstream', 'redirect']
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
    _filters: RouteFilter[] = [];
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

    filterForm = new FormGroup({
        filter: new FormControl<RouteFilter>({} as RouteFilter)
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
        methods: new FormControl<Array<string>>(['GET', 'POST','PUT', 'PATCH', 'DELETE']),
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
        type: new FormControl<string>("upstream"),
        filters: new FormControl<Array<RouteFilter>>([]),
    });

    constructor(
        private dialogRef: MatDialogRef<any>,
        private upstreamService: UpstreamService,
        private staticService: StaticService,
        private sensorService: SensorService,
        private routeFilterService: RoutefilterService,
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
        this.routeFilterService.get().subscribe(data => {
            this._filters = data.data;
        });
        this.isAddMode = !this.routeData;
        if (!this.isAddMode) {
            this.form.get('name')?.setValue(this.routeData.name);
            this.form.get('upstream')?.setValue(this.routeData.upstream);
            this.form.get('static')?.setValue(this.routeData.static);
            this.form.get('redirect')?.setValue(this.routeData.redirect);
            this.form.get('paths')?.setValue(this.routeData.paths);
            this.form.get('methods')?.setValue(this.routeData.methods);
            if (this.routeData.allowed_methods) {
                this.form.get('allowed_methods')?.setValue(this.routeData.allowed_methods);
            } else {
                this.form.get('allowed_methods')?.setValue(['GET', 'HEAD', 'POST', 'OPTIONS', 'PUT', 'PATCH', 'DELETE']);
            }
            if (this.routeData.allowed_content_type) {
                this.form.get('allowed_content_type')?.setValue(this.routeData.allowed_content_type);
            } else {
                this.form.get('allowed_content_type')?.setValue([
                    'application/x-www-form-urlencoded',
                    'multipart/form-data',
                    'text/xml',
                    'application/xml',
                    'application/soap+xml',
                    'application/json'
                ]);
            }
            this.form.get('monitor_only')?.setValue(this.routeData.monitor_only);
            this.form.get('sensor')?.setValue(this.routeData.sensor);
            this.form.get('type')?.setValue(this.routeData.type);
            if (this.routeData.cache_methods) {
                this.form.get('cache_methods')?.setValue(this.routeData.cache_methods);
            } else {
                this.form.get('cache_methods')?.setValue([]);
            }
            if (this.routeData.filters) {
                this.form.get('filters')?.setValue(this.routeData.filters);
            } else {
                this.form.get('filters')?.setValue([]);
            }
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

    onAddFilter(): void {
        let data = this.filterForm.value.filter as RouteFilter;
        this.form.value.filters?.push(data);
        this.filterForm.reset();
    }

    onRemoveFilter(keyword: any): void {
        if (this.form.value.filters != null) {
            let index = this.form.value.filters.indexOf(keyword);
            if (index >= 0) {
                this.form.value.filters.splice(index, 1);
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
        return object1 && object2 && object1._id === object2._id;
    }

    get f(): { [key: string]: AbstractControl } {
        return this.form.controls;
    }
}