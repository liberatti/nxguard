import { Component, OnInit } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
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
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { RuleCategory, SecRule, Sensor } from 'app/models/sensor';
import { Feed } from 'app/models/feed';
import { NotificationService } from 'app/services/notification.service';
import { OAuthService } from 'app/services/oauth.service';
import { FeedService } from 'app/services/feed.service';
import { RuleCategoryService, SensorService } from 'app/services/sensor.service';
import { DefaultPageMeta } from 'app/models/shared';
import { CommonModule } from '@angular/common';
import { FormaterService } from "app/services/formater.service";
import { MatMomentDateModule } from "@angular/material-moment-adapter";

import { MatExpansionModule } from '@angular/material/expansion';

@Component({
    selector: 'app-sensor-form',
    standalone: true,
    imports: [RouterModule, CommonModule,
        ReactiveFormsModule, TranslatePipe,
        MatMomentDateModule, MatSidenavModule, MatIconModule, MatButtonModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule, MatTabsModule, MatGridListModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule, MatSlideToggleModule, MatCheckboxModule,
        MatFormFieldModule, MatChipsModule, MatExpansionModule],
    templateUrl: './sensor-form.component.html'
})
export class SensorFormComponent implements OnInit {
    isAddMode: boolean;
    submitted = false;
    selectedTabIndex = 0;
    breakpoint: number;
    _categories: RuleCategory[] = [];
    _rbl_feeds: Feed[] = [];
    _geo_countries: string[] = [
        "US", "CA", "BR", "IN", "GB", "AU", "DE", "FR", "IT", "ES",
        "JP", "CN", "MX", "RU", "ZA", "KR", "NG", "AR", "SE", "NO",
        "DK", "FI", "PL", "CH", "NL", "BE", "SG", "AE", "MY", "TH",
        "PH", "NG", "KR", "None", "Unknown"
    ];
    _allowed_http_versions: string[] = [
        'HTTP/1.0', 'HTTP/1.1', 'HTTP/2', 'HTTP/2.0'
    ];
    _restricted_extensions: string[] = [
        '.asa/', '.asax/', '.ascx/', '.axd/', '.backup/', '.bak/', '.bat/', '.cdx/', '.cer/',
        '.cfg/', '.cmd/', '.com/', '.config/', '.conf/', '.cs/', '.csproj/', '.csr/', '.dat/',
        '.db/', '.dbf/', '.dll/', '.dos/', '.htr/', '.htw/', '.ida/', '.idc/', '.idq/',
        '.inc/', '.ini/', '.key/', '.licx/', '.lnk/', '.log/', '.mdb/', '.old/', '.pass/',
        '.pdb/', '.pol/', '.printer/', '.pwd/', '.rdb/', '.resources/', '.resx/', '.sql/',
        '.swp/', '.sys/', '.vb/', '.vbs/', '.vbproj/', '.vsdisco/', '.webinfo/', '.xsd/', '.xsx/'
    ];
    ruleDC: string[] = ['code', 'severity', 'msg', 'actionSummary', 'action'];
    ruleDS: MatTableDataSource<SecRule>;
    ruleCH: number[] = [];

    form = new FormGroup({
        _id: new FormControl<string>(''),
        name: new FormControl<string>('', {
            validators: [
                Validators.required,
                Validators.minLength(4),
            ],
        }),
        description: new FormControl<string>(''),
        categories: new FormControl<Array<string>>([]),
        exclusions: new FormControl<Array<number>>([]),
        security: new FormGroup({
            geo_codes: new FormControl<string[]>([]),
            reputation: new FormControl<string[]>([]),
            trusted: new FormControl<string[]>([])
        }),
        inspection: new FormGroup({
            level: new FormControl<number>(1),
            score: new FormGroup({
                inbound: new FormControl<number>(5),
                outbound: new FormControl<number>(4)
            }),
            variables: new FormGroup({
                allowed_http_versions: new FormControl<string[] | string>([
                    'HTTP/1.0', 'HTTP/1.1', 'HTTP/2', 'HTTP/2.0'
                ]),
                max_file_size: new FormControl<number>(26214400),
                restricted_extensions: new FormControl<string[] | string>([
                    '.asa/', '.asax/', '.ascx/', '.axd/', '.backup/', '.bak/', '.bat/', '.cdx/', '.cer/',
                    '.cfg/', '.cmd/', '.com/', '.config/', '.conf/', '.cs/', '.csproj/', '.csr/', '.dat/',
                    '.db/', '.dbf/', '.dll/', '.dos/', '.htr/', '.htw/', '.ida/', '.idc/', '.idq/',
                    '.inc/', '.ini/', '.key/', '.licx/', '.lnk/', '.log/', '.mdb/', '.old/', '.pass/',
                    '.pdb/', '.pol/', '.printer/', '.pwd/', '.rdb/', '.resources/', '.resx/', '.sql/',
                    '.swp/', '.sys/', '.vb/', '.vbs/', '.vbproj/', '.vsdisco/', '.webinfo/', '.xsd/', '.xsx/'
                ]),
                max_num_args: new FormControl<number>(255),
                arg_name_length: new FormControl<number>(100),
                arg_length: new FormControl<number>(2000)
            })
        })
    });

    constructor(
        private notificationService: NotificationService,
        private route: ActivatedRoute,
        private router: Router,
        private sensorService: SensorService,
        private ruleCatService: RuleCategoryService,
        private feedService: FeedService,
        protected oauth: OAuthService,
        protected formater: FormaterService
    ) {
        this.breakpoint = (window.innerWidth <= 600) ? 2 : 8;
        this.isAddMode = false;
        this.ruleDS = new MatTableDataSource<SecRule>;
    }

    ngOnInit(): void {
        const { id } = this.route.snapshot.params;
        this.isAddMode = !id;

        if (!this.oauth.isRole('superuser')) {
            this.form.disable();
        }

        if (!this.isAddMode) {
            this.sensorService.getById(id).subscribe((data: Sensor) => {
                this.form.patchValue(data);
            });
        }

        this.getCategories(null);
        this.getFeeds(null);
    }

    getGeoCodes(): string[] {
        return (this.form.get('security.geo_codes')?.value as string[]) || [];
    }

    getReputation(): string[] {
        return (this.form.get('security.reputation')?.value as string[]) || [];
    }

    getTrusted(): string[] {
        return (this.form.get('security.trusted')?.value as string[]) || [];
    }

    onSave() {
        this.submitted = true;
        if (this.form.status === "INVALID") {
            return;
        }

        const payload = this.form.value as Sensor;

        if (this.isAddMode) {
            delete payload._id;
            this.sensorService.save(payload).subscribe(() => {
                this.notificationService.openSnackBar('Sensor saved');
                this.router.navigate(['/sensor']);
            });
        } else {
            this.sensorService.update(String(payload._id), payload).subscribe(() => {
                this.notificationService.openSnackBar('Sensor updated');
                this.router.navigate(['/sensor']);
            });
        }
    }

    isRuleSelected(code: number): boolean {
        return this.ruleCH.includes(code);
    }

    selectRule(checked: boolean, code: number) {
        if (checked) {
            this.ruleCH.push(code);
        } else {
            let idx = this.ruleCH.indexOf(code);
            if (idx >= 0) this.ruleCH.splice(idx, 1);
        }
    }

    selectAllRules(checked: boolean) {
        if (checked) {
            for (let i = 0; i < this.ruleDS.data.length; i++) {
                if (!this.ruleCH.includes(this.ruleDS.data[i].code)) {
                    this.ruleCH.push(this.ruleDS.data[i].code);
                }
            }
        } else {
            this.ruleCH = [];
        }
    }

    getFeeds(event: any) {
        if (event === null) {
            this.feedService.get(new DefaultPageMeta()).subscribe((data: any) => {
                const list = Array.isArray(data) ? data : (data?.data || []);
                const allowedTypes = ['reputation', 'bypass', 'by_pass', 'network', 'network_static', 'ip', 'rbl', 'cidr'];
                this._rbl_feeds = list.filter((item: any) =>
                    !item['type'] || allowedTypes.includes(item['type'])
                );
            });
        }
    }

    onAddBlock(event: any): void {
        let val = event.value;
        if (typeof val === 'object' && val) val = val.name || val._id;
        let list = [...this.getReputation()];
        if (val && !list.includes(val)) {
            list.push(val);
            this.form.get('security.reputation')?.setValue(list);
        }
    }

    onAddPermit(event: any): void {
        let val = event.value;
        if (typeof val === 'object' && val) val = val.name || val._id;
        let list = [...this.getTrusted()];
        if (val && !list.includes(val)) {
            list.push(val);
            this.form.get('security.trusted')?.setValue(list);
        }
    }

    onRemovePermit(keyword: string): void {
        let list = [...this.getTrusted()];
        let index = list.indexOf(keyword);
        if (index >= 0) {
            list.splice(index, 1);
            this.form.get('security.trusted')?.setValue(list);
        }
        this.form.markAsTouched();
    }

    onRemoveBlock(keyword: string): void {
        let list = [...this.getReputation()];
        let index = list.indexOf(keyword);
        if (index >= 0) {
            list.splice(index, 1);
            this.form.get('security.reputation')?.setValue(list);
        }
    }

    onAddGeo(event: any): void {
        let data = event.value as string;
        let list = [...this.getGeoCodes()];
        if (data && !list.includes(data)) {
            list.push(data);
            this.form.get('security.geo_codes')?.setValue(list);
        }
    }

    onRemoveGeo(keyword: string): void {
        let list = [...this.getGeoCodes()];
        let index = list.indexOf(keyword);
        if (index >= 0) {
            list.splice(index, 1);
            this.form.get('security.geo_codes')?.setValue(list);
        }
    }

    getVariableList(field: string): string[] {
        const varsGroup = this.form.get('inspection.variables') as FormGroup;
        const val: any = varsGroup?.get(field)?.value;
        if (!val) return [];
        if (Array.isArray(val)) return val as string[];
        if (typeof val === 'string') {
            const str: string = val;
            return str.trim().split(/\s+/).filter((x: string) => x.length > 0);
        }
        return [];
    }

    filterActiveVariable(options: string[], field: string): string[] {
        if (!options) return [];
        const current = this.getVariableList(field);
        return options.filter(item => !current.includes(item));
    }

    onAddVariableItem(field: string, event: any): void {
        const val = event.value as string;
        const list = [...this.getVariableList(field)];
        if (val && !list.includes(val)) {
            list.push(val);
            const varsGroup = this.form.get('inspection.variables') as FormGroup;
            varsGroup?.get(field)?.setValue(list);
            this.form.markAsTouched();
        }
    }

    onRemoveVariableItem(field: string, item: string): void {
        const list = [...this.getVariableList(field)];
        const index = list.indexOf(item);
        if (index >= 0) {
            list.splice(index, 1);
            const varsGroup = this.form.get('inspection.variables') as FormGroup;
            varsGroup?.get(field)?.setValue(list);
            this.form.markAsTouched();
        }
    }

    getCategories(event: any) {
        if (event === null) {
            this.ruleCatService.getByPhases().subscribe((data: any) => {
                this._categories = Array.isArray(data) ? data : (data?.data || []);
            });
        } else {
            const name = event?.target?.value || '';
            if (name) {
                this.ruleCatService.getByNameAndPhases(name, []).subscribe((data: any) => {
                    this._categories = Array.isArray(data) ? data : (data?.data || []);
                });
            } else {
                this.ruleCatService.getByPhases().subscribe((data: any) => {
                    this._categories = Array.isArray(data) ? data : (data?.data || []);
                });
            }
        }
    }

    onAddCategory(event: any): void {
        let data = event.value as RuleCategory;
        let cats = this.form.value.categories || [];
        if (data && data.name && !cats.includes(data.name)) {
            cats.push(data.name);
            this.form.patchValue({ categories: cats });
        }
    }

    onSelectCategory(cat_name: string): void {
        this.ruleCatService.getBySingleName(cat_name).subscribe((data: any) => {
            if (!data) return;
            const categoryData = data.data || data;
            const ruleList = Array.isArray(categoryData) ? categoryData : (categoryData.rules || []);
            this.ruleDS.data = ruleList;
            this.ruleCH = [];
        });
    }

    onRemoveCategory(keyword: any): void {
        if (this.form.value.categories != null) {
            let index = this.form.value.categories.indexOf(keyword);
            if (index >= 0) {
                this.form.value.categories.splice(index, 1);
            }
        }
    }

    isRuleActive(code: number) {
        let exclusions = (this.form.value.exclusions as Array<number>) || [];
        return !exclusions.includes(code);
    }

    onRuleCheck(checked: boolean, code: number) {
        let exclusions = (this.form.value.exclusions as Array<number>) || [];
        if (checked) {
            let idx = exclusions.indexOf(code);
            if (idx >= 0) exclusions.splice(idx, 1);
        } else {
            if (!exclusions.includes(code)) {
                exclusions.push(code);
            }
        }
        this.form.get('exclusions')?.reset(exclusions);
    }

    filterActiveCategory(arr1: Array<any>, arr2: Array<any> | null | undefined): Array<any> {
        if (!arr1 || !Array.isArray(arr1)) return [];
        if (arr2 && Array.isArray(arr2))
            return arr1.filter(itemA => itemA && !arr2.some(itemB => itemB === itemA['name']));
        return arr1;
    }

    filterActiveGeo(geo: string[]): string[] {
        if (!geo) return [];
        const geoCodes = this.getGeoCodes();
        return geo.filter(code => !geoCodes.includes(code));
    }

    filterActiveFeed(feeds: Array<Feed>): Array<Feed> {
        if (!feeds) return [];
        const used = [...this.getReputation(), ...this.getTrusted()];
        return feeds.filter(a =>
            a && !used.includes(a.name) && !used.includes(a._id)
        );
    }

    compareFn(object1: any, object2: any) {
        if (!object1 || !object2) return object1 === object2;
        return (object1._id || object1) === (object2._id || object2);
    }
}
