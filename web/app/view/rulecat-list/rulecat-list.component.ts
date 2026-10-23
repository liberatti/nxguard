import { AfterViewInit, Component, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatChipsModule } from '@angular/material/chips';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressBarModule } from '@angular/material/progress-bar';

import { RuleCategory } from '../../models/sensor';
import { RuleCategoryService } from '../../services/sensor.service';
import { NotificationService } from '../../services/notification.service';
import { OAuthService } from '../../services/oauth.service';
import { ConfirmDialogComponent } from '../../components/confirm-dialog/confirm-dialog.component';

@Component({
    selector: 'app-rulecat-list',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        ReactiveFormsModule,
        RouterModule,
        TranslatePipe,
        MatCardModule,
        MatTableModule,
        MatPaginatorModule,
        MatSortModule,
        MatButtonModule,
        MatIconModule,
        MatFormFieldModule,
        MatInputModule,
        MatChipsModule,
        MatMenuModule,
        MatTooltipModule,
        MatDialogModule,
        MatSelectModule,
        MatProgressBarModule
    ],
    templateUrl: './rulecat-list.component.html',
    styleUrl: './rulecat-list.component.css'
})
export class RuleCategoryListComponent implements OnInit, AfterViewInit {
    displayedColumns: string[] = ['_id', 'name', 'phase', 'scope', 'seq', 'system', 'action'];
    dataSource = new MatTableDataSource<RuleCategory>([]);
    isLoading = false;
    searchQuery = '';
    selectedPhase: number | null = null;

    @ViewChild(MatPaginator) paginator!: MatPaginator;
    @ViewChild(MatSort) sort!: MatSort;

    constructor(
        private ruleCatService: RuleCategoryService,
        private notificationService: NotificationService,
        private dialog: MatDialog,
        protected oauth: OAuthService
    ) {}

    ngOnInit(): void {
        this.loadCategories();
    }

    ngAfterViewInit(): void {
        this.dataSource.paginator = this.paginator;
        this.dataSource.sort = this.sort;
        this.dataSource.filterPredicate = (data: RuleCategory, filter: string) => {
            const term = filter.trim().toLowerCase();
            const idMatch = (data._id || '').toLowerCase().includes(term);
            const nameMatch = (data.name || '').toLowerCase().includes(term);
            const fileMatch = (data.file || '').toLowerCase().includes(term);
            const scopeMatch = (data.scope || '').toLowerCase().includes(term);
            const phaseMatch = String(data.phase || '').includes(term);
            return idMatch || nameMatch || fileMatch || scopeMatch || phaseMatch;
        };
    }

    loadCategories(): void {
        this.isLoading = true;
        this.ruleCatService.getAll().subscribe({
            next: (data: RuleCategory[]) => {
                this.dataSource.data = data;
                this.isLoading = false;
            },
            error: () => {
                this.isLoading = false;
            }
        });
    }

    applyFilter(event?: Event): void {
        if (event) {
            const filterValue = (event.target as HTMLInputElement).value;
            this.searchQuery = filterValue;
        }
        this.dataSource.filter = this.searchQuery.trim().toLowerCase();
        if (this.dataSource.paginator) {
            this.dataSource.paginator.firstPage();
        }
    }

    clearFilter(): void {
        this.searchQuery = '';
        this.dataSource.filter = '';
        if (this.dataSource.paginator) {
            this.dataSource.paginator.firstPage();
        }
    }

    onRemove(item: RuleCategory): void {
        const dialogRef = this.dialog.open(ConfirmDialogComponent, {
            data: {
                title: 'RULECAT.CONFIRM_DELETE_TITLE',
                message: `${item.name} (${item._id || ''})`
            }
        });

        dialogRef.afterClosed().subscribe((result: boolean) => {
            if (result && item._id) {
                this.ruleCatService.removeById(item._id).subscribe({
                    next: () => {
                        this.notificationService.openSnackBar('RULECAT.NOTIFICATIONS.REMOVED');
                        this.loadCategories();
                    }
                });
            }
        });
    }

    getPhaseLabel(phase?: number): string {
        switch (phase) {
            case 1: return 'P1';
            case 2: return 'P2';
            case 3: return 'P3';
            case 4: return 'P4';
            case 5: return 'P5';
            case 6: return 'P6';
            default: return phase !== undefined ? `P${phase}` : '-';
        }
    }

    getPhaseTooltip(phase?: number): string {
        return phase ? `RULECAT.PHASES.${phase}` : '';
    }
}
