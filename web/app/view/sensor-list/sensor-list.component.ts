import {Component, OnInit} from '@angular/core';
import {MatTableDataSource, MatTableModule} from '@angular/material/table';
import {MatPaginatorModule, PageEvent} from '@angular/material/paginator';
import {MatDialog} from '@angular/material/dialog';
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
import {Sensor} from 'app/models/sensor';
import {SensorService} from 'app/services/sensor.service';
import {NotificationService} from 'app/services/notification.service';
import {DefaultPageMeta} from 'app/models/shared';
import {OAuthService} from "../../services/oauth.service";

@Component({
    selector: 'app-sensor-list',
    standalone: true,
    imports: [RouterModule, CommonModule,
        FormsModule,
        ReactiveFormsModule, TranslatePipe,
        MatMomentDateModule,
        MatSidenavModule, MatIconModule, MatButtonModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule,
        MatFormFieldModule, MatChipsModule],
    templateUrl: './sensor-list.component.html'
})

export class SensorListComponent implements OnInit {
    sensorDC: string[] = ['name', 'description', 'action'];
    sensorDS: MatTableDataSource<Sensor>;
    sensorPA = new DefaultPageMeta();
    searchQuery: string = '';

    constructor(
        private notificationService: NotificationService,
        private sensorService: SensorService,
        private confirmDialog: MatDialog,
        protected oauth: OAuthService,
    ) {
        this.sensorDS = new MatTableDataSource<Sensor>;
    }

    ngOnInit(): void {
        this.updateGridTable();
    }

    applyFilter(): void {
        this.sensorPA.page = 1;
        this.updateGridTable();
    }

    clearFilter(): void {
        this.searchQuery = '';
        this.applyFilter();
    }

    updateGridTable() {
        this.sensorService.get(this.sensorPA, this.searchQuery).subscribe({
            next: (data) => {
                if (data && data.metadata) {
                    this.sensorDS.data = data.data || [];
                    this.sensorPA.total_elements = data.metadata.total_elements;
                } else {
                    this.sensorDS.data = [];
                    this.sensorPA.total_elements = 0;
                }
            },
            error: () => {
                this.sensorDS.data = [];
                this.sensorPA.total_elements = 0;
            }
        });
    }

    nextPage(event: PageEvent) {
        this.sensorPA.page = event.pageIndex + 1;
        this.sensorPA.per_page = event.pageSize;
        this.updateGridTable();
    }

    onSave() {
        this.sensorService.get(this.sensorPA).subscribe(data => {
            this.updateGridTable();
        });
    }

    onRemove(dto: Sensor) {
        const dialogRef = this.confirmDialog.open(ConfirmDialogComponent, {
            data: {title: "Confirm sensor removal ", message: "Remove " + dto.name},
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result && dto._id) {
                this.sensorService.removeById(dto._id).subscribe(() => {
                    this.updateGridTable();
                    this.notificationService.openSnackBar('Sensor removed');
                });
            }
        });
    }
}