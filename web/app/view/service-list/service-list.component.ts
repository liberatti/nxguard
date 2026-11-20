import {Component, OnInit} from '@angular/core';
import {MatTableDataSource, MatTableModule} from '@angular/material/table';
import {MatPaginatorModule, PageEvent} from '@angular/material/paginator';
import {MatDialog} from '@angular/material/dialog';
import {MatSlideToggleChange, MatSlideToggleModule} from '@angular/material/slide-toggle';
import {BreakpointObserver} from '@angular/cdk/layout';
import {DefaultPageMeta} from 'app/models/shared';
import {CommonModule} from '@angular/common';
import {FormsModule, ReactiveFormsModule} from '@angular/forms';
import {MatMomentDateModule} from '@angular/material-moment-adapter';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatChipsModule} from '@angular/material/chips';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatIconModule} from '@angular/material/icon';
import {MatInputModule} from '@angular/material/input';
import {MatListModule} from '@angular/material/list';
import {MatMenuModule} from '@angular/material/menu';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {MatSelectModule} from '@angular/material/select';
import {MatSidenavModule} from '@angular/material/sidenav';
import {MatSortModule} from '@angular/material/sort';
import {MatTooltipModule} from '@angular/material/tooltip';
import {RouterModule} from '@angular/router';
import {TranslatePipe} from '@ngx-translate/core';
import {ConfirmDialogComponent} from 'app/components/confirm-dialog/confirm-dialog.component';
import {Service, Route} from 'app/models/service';
import {ServiceService} from 'app/services/service.service';
import {NotificationService} from 'app/services/notification.service';
import {OAuthService} from "../../services/oauth.service";

@Component({
    selector: 'app-service-list',
    standalone: true,
    imports: [RouterModule, CommonModule,
        FormsModule,
        ReactiveFormsModule, TranslatePipe,
        MatMomentDateModule,
        MatSidenavModule, MatIconModule, MatButtonModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule, MatSlideToggleModule,
        MatFormFieldModule, MatChipsModule],
    templateUrl: './service-list.component.html',
    styleUrl: './service-list.component.css'
})

export class ServiceListComponent implements OnInit {
    serviceDC: string[] = ['name', 'sans', 'routes', 'action'];
    serviceDS: MatTableDataSource<Service>;
    servicePA = new DefaultPageMeta();
    searchQuery: string = '';
    isLoading: boolean = false;

    constructor(
        private notificationService: NotificationService,
        private serviceService: ServiceService,
        private confirmDialog: MatDialog,
        private responsive: BreakpointObserver,
        protected oauth: OAuthService,
    ) {
        this.serviceDS = new MatTableDataSource<Service>;
    }

    ngOnInit(): void {
        this.updateGridTable();
    }

    applyFilter(): void {
        this.servicePA.page = 1;
        this.updateGridTable();
    }

    clearFilter(): void {
        this.searchQuery = '';
        this.applyFilter();
    }

    updateGridTable() {
        this.isLoading = true;
        this.serviceService.get(this.servicePA, this.searchQuery).subscribe({
            next: (data) => {
                this.isLoading = false;
                if (data && data.metadata) {
                    this.serviceDS.data = data.data || [];
                    this.servicePA.total_elements = data.metadata.total_elements;
                } else {
                    this.serviceDS.data = [];
                    this.servicePA.total_elements = 0;
                }
            },
            error: () => {
                this.isLoading = false;
                this.serviceDS.data = [];
                this.servicePA.total_elements = 0;
            }
        });
    }

    onSave() {
        this.serviceService.get(this.servicePA).subscribe(() => {
            this.updateGridTable();
        });
    }

    onRemove(dto: Service) {
        const dialogRef = this.confirmDialog.open(ConfirmDialogComponent, {
            data: {title: "Confirm service removal ", message: "Remove " + dto.name},
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result && dto._id) {
                this.serviceService.removeById(dto._id).subscribe(() => {
                    this.updateGridTable();
                    this.notificationService.openSnackBar('Service removed');
                });
            }
        });
    }

    nextPage(event: PageEvent) {
        this.servicePA.page = event.pageIndex + 1;
        this.servicePA.per_page = event.pageSize;
        this.updateGridTable();
    }

    toggleServiceActive(i: number, e: MatSlideToggleChange) {
        const service = {
            _id: this.serviceDS.data[i]['_id'],
            active: e.checked
        } as Partial<Service>;

        this.serviceService.patch(service['_id'] as string, service).subscribe({
            next: () => {
                this.updateGridTable();
            },
            error: () => {
                this.updateGridTable();
            }
        });
    }

    getPrimarySans(element: Service): string[] {
        if (!element.sans || element.sans.length === 0) return [];
        return element.sans.slice(0, 2);
    }

    getRemainingSansCount(element: Service): number {
        if (!element.sans || element.sans.length <= 2) return 0;
        return element.sans.length - 2;
    }

    getAllSansTooltip(element: Service): string {
        if (!element.sans) return '';
        return element.sans.join('\n');
    }

    getPrimaryRoutes(element: Service): Route[] {
        if (!element.routes || element.routes.length === 0) return [];
        return element.routes.slice(0, 2);
    }

    getRemainingRoutesCount(element: Service): number {
        if (!element.routes || element.routes.length <= 2) return 0;
        return element.routes.length - 2;
    }

    getAllRoutesTooltip(element: Service): string {
        if (!element.routes || element.routes.length === 0) return '';
        return element.routes.map(r => {
            const type = r.type || 'UPSTREAM';
            const upstream = r.upstream?.name ? ` -> ${r.upstream.name}` : '';
            return `${r.name} (${type})${upstream}`;
        }).join('\n');
    }

    getRouteTooltip(r: Route): string {
        const parts: string[] = [];
        if (r.name) parts.push(`Route: ${r.name}`);
        if (r.type) parts.push(`Type: ${r.type}`);
        if (r.upstream?.name) parts.push(`Upstream: ${r.upstream.name}`);
        if (r.paths && r.paths.length > 0) parts.push(`Paths: ${r.paths.join(', ')}`);
        return parts.join('\n');
    }
}