import {Component, OnInit, signal, ViewChild} from '@angular/core';
import {MatTableDataSource, MatTableModule} from '@angular/material/table';
import {MatPaginatorModule, PageEvent} from '@angular/material/paginator';
import {MatDialog} from '@angular/material/dialog';
import {BreakpointObserver, Breakpoints} from '@angular/cdk/layout';
import {CommonModule} from '@angular/common';
import {FormControl, FormGroup, FormsModule, ReactiveFormsModule} from '@angular/forms';
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
import {MatSlideToggleModule} from '@angular/material/slide-toggle';
import {MatSortModule} from '@angular/material/sort';
import {MatTooltipModule} from '@angular/material/tooltip';
import {RouterModule} from '@angular/router';
import {TranslatePipe} from '@ngx-translate/core';
import {DefaultPageMeta} from 'app/models/shared';
import {TransactionFilter, TransactionLog} from 'app/models/transaction';
import {TransactionService} from 'app/services/transaction.service';
import {DateFormatPipe} from 'app/pipes/date_format.pipe';
import {ByteFormatPipe} from 'app/pipes/format_bytes.pipe';
import Chart from 'chart.js/auto';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import 'chartjs-adapter-moment';
import moment from 'moment';
import Zoom from 'chartjs-plugin-zoom';
import {FormaterService} from 'app/services/formater.service';
import {MatTabsModule} from '@angular/material/tabs';
import {MatDatepickerModule} from '@angular/material/datepicker';
import {MatButtonToggleModule} from '@angular/material/button-toggle';
import {MatGridListModule} from '@angular/material/grid-list';
import {MatExpansionModule} from '@angular/material/expansion';
import {animate, state, style, transition, trigger} from '@angular/animations';
import {TimeFormatPipe} from 'app/pipes/format_time.pipe';
import {TransactionRAWDialogComponent} from 'app/components/transaction-raw-dialog/transaction-raw-dialog.component';
import {TransactionFilterDialogComponent} from 'app/components/transaction-filter-dialog/transaction-filter-dialog.component';
import {MatRipple} from "@angular/material/core";
import {RuleDetailsDialogComponent} from "../../components/rule-details-dialog/rule-details-dialog.component";
import {RuleService} from "../../services/sensor.service";
import {MatSnackBar} from '@angular/material/snack-bar';
import {MatSnackBarModule} from '@angular/material/snack-bar';
import {HighlightModule} from 'ngx-highlightjs';
import {HighlightLineNumbers} from 'ngx-highlightjs/line-numbers';
import {DateRangeDialogComponent} from 'app/components/date-range-dialog/date-range-dialog.component';

@Component({
    selector: 'app-transaction-list',
    standalone: true,
    animations: [
        trigger('detailExpand', [
            state('collapsed, void', style({ height: '0px', minHeight: '0', display: 'none' })),
            state('expanded', style({ height: '*' })),
            transition(
                'expanded <=> collapsed',
                animate('225ms cubic-bezier(0.4, 0.0, 0.2, 1)')
            ),
        ]),
    ],
    imports: [RouterModule, CommonModule, MatButtonToggleModule,
        ReactiveFormsModule, TranslatePipe, MatTabsModule, MatDatepickerModule,
        MatMomentDateModule, ByteFormatPipe, DateFormatPipe, TimeFormatPipe,
        MatSidenavModule, MatIconModule, MatButtonModule, MatGridListModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule, MatExpansionModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule, MatSlideToggleModule,
        MatFormFieldModule, MatChipsModule, MatRipple, FormsModule, MatSnackBarModule],
    templateUrl: './transaction-list.component.html',
    styleUrl: './transaction-list.component.css',
})

export class TransactionListComponent implements OnInit {
    readonly panelOpenState = signal(false);
    input_regex: string = "";
    logtime_start: Date = moment().subtract(1, 'day').toDate();
    logtime_end: Date = moment().toDate();
    form = new FormGroup({
        start: new FormControl<Date>(moment().subtract(1, 'day').toDate()),
        end: new FormControl<Date>(moment().toDate()),
        filters: new FormControl<Array<string>>([]),
    });

    get formattedDateRange(): string {
        const start = this.form.get('start')?.value;
        const end = this.form.get('end')?.value;
        if (!start || !end) return 'Select Date Range';
        const startM = moment(start);
        const endM = moment(end);
        
        if (startM.isSame(endM, 'day')) {
            return `${startM.format('DD/MM/YYYY HH:mm')} - ${endM.format('HH:mm')}`;
        }
        return `${startM.format('DD/MM/YY HH:mm')} - ${endM.format('DD/MM/YY HH:mm')}`;
    }

    transactionDC: string[] = ['expand', 'logtime', 'score', 'source', 'service', 'request_line', 'duration'];
    transactionDS: MatTableDataSource<TransactionLog>;
    transactionPA = new DefaultPageMeta();
    transactions: Array<TransactionLog> = [];
    currentRowSelected: TransactionLog = {} as TransactionLog;
    expandedElement: TransactionLog | null = null;

    chart: any;
    chartConfig = {
        type: 'line',
        plugins: [ChartDataLabels],
        data: {
            labels: [],
            datasets: [
                {
                    label: "TPM",
                    data: [],
                    borderColor: '#0284c7',
                    backgroundColor: 'rgba(2, 132, 199, 0.15)',
                    fill: true,
                    tension: 0.3,
                    borderWidth: 2,
                    pointRadius: 2,
                    pointHoverRadius: 5,
                }
            ]
        },
        options: {
            layout: {
                padding: 5
            },
            aspectRatio: 1.5,
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                datalabels: {
                    display: false
                },
                zoom: {
                    zoom: {
                        drag: {
                            enabled: true
                        },
                        mode: 'x',
                        onZoomComplete: (chartUpdate: any) => {
                            const xAxis = chartUpdate['chart'].scales['x'];
                            this.form.get('start')?.setValue(xAxis.min);
                            this.form.get('end')?.setValue(xAxis.max);
                            this.onSearch();
                        },
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                    },
                    ticks: {
                        color: '#64748b',
                        font: { size: 11 },
                        autoSkip: true,
                        autoSkipPadding: 50,
                        maxRotation: 0
                    },
                    time: {
                        unit: 'day',
                        displayFormats: {
                            day: 'dd',
                            hour: 'HH:mm',
                            minute: 'HH:mm',
                            second: 'HH:mm:ss'
                        }
                    },
                    border: {
                        display: false
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                    },
                    ticks: {
                        color: '#64748b',
                        font: { size: 11 },
                        callback: (value: any) => {
                            return this.formatService.tpm(value);
                        }
                    },
                    beginAtZero: true,
                    border: {
                        display: false
                    }
                }
            }
        },
    } as any;

    constructor(
        private transactionService: TransactionService,
        private confirmDialog: MatDialog,
        private responsive: BreakpointObserver,
        private formatService: FormaterService,
        private ruleService: RuleService,
        private snackBar: MatSnackBar
    ) {
        Chart.register(ChartDataLabels);
        Chart.register(Zoom);
        this.transactionDS = new MatTableDataSource<TransactionLog>;
        this.responsive.observe([Breakpoints.Small])
            .subscribe(result => {
                if (result.breakpoints[Breakpoints.Small]) {
                    this.transactionDC = ['expand', 'logtime', 'source', 'service', 'request_line'];
                }
            });
    }

    isRowExpanded(row: any): boolean {
        if (!row || !this.expandedElement) return false;
        if (row === this.expandedElement) return true;
        if (row._id && this.expandedElement._id) {
            return row._id === this.expandedElement._id;
        }
        if (row.unique_id && this.expandedElement.unique_id) {
            return row.unique_id === this.expandedElement.unique_id;
        }
        return false;
    }

    expandCollapse(row: any) {
        if (!row) return;
        if (this.isRowExpanded(row)) {
            this.expandedElement = null;
            this.currentRowSelected = {} as TransactionLog;
        } else {
            this.expandedElement = row;
            this.currentRowSelected = row;
        }
    }

    ngOnInit(): void {
        this.onSearch();
    }

    onRefresh(): void {
        const now = moment().toDate();
        const start = this.form.get('start')?.value;
        const end = this.form.get('end')?.value;
        if (start && end) {
            const durationMs = moment(end).diff(moment(start));
            if (durationMs > 0 && durationMs <= 7 * 24 * 60 * 60 * 1000) {
                this.form.get('start')?.setValue(moment(now).subtract(durationMs, 'milliseconds').toDate());
                this.form.get('end')?.setValue(now);
            } else {
                this.form.get('end')?.setValue(now);
            }
        }
        this.onSearch();
    }

    openDateRangeDialog(): void {
        const dialogRef = this.confirmDialog.open(DateRangeDialogComponent, {
            width: '640px',
            maxWidth: '95vw',
            data: {
                start: this.form.get('start')?.value,
                end: this.form.get('end')?.value,
            }
        });

        dialogRef.afterClosed().subscribe((result: { start: Date; end: Date } | undefined) => {
            if (result) {
                this.form.get('start')?.setValue(result.start);
                this.form.get('end')?.setValue(result.end);
                this.onSearch();
            }
        });
    }

    onSearch() {
        let filter = this.form.value as TransactionFilter;
        this.transactionService.getTpm(filter).subscribe({
            next: (data) => {
                if (this.chart != null) {
                    this.chart.destroy();
                }
                this.chart = new Chart("trn-chart", this.chartConfig);
                this.chart.data.labels = [];
                this.chart.data.datasets[0].data = [];
                if (data && Array.isArray(data)) {
                    for (let i = 0; i < data.length; i++) {
                        this.chart.data.labels.push(moment(data[i].logtime));
                        this.chart.data.datasets[0].data.push(data[i].count);
                    }
                }
                this.chart.update();
            },
            error: () => {
                if (this.chart != null) {
                    this.chart.destroy();
                }
                this.chart = new Chart("trn-chart", this.chartConfig);
                this.chart.data.labels = [];
                this.chart.data.datasets[0].data = [];
                this.chart.update();
            }
        });

        this.transactionService.search(filter, this.transactionPA).subscribe({
            next: (data) => {
                const list = (data && data.data) ? data.data : [];
                this.transactions = list;
                this.transactionDS.data = list;
                if (data && data.metadata) {
                    this.transactionPA = data.metadata;
                } else {
                    this.transactionPA = new DefaultPageMeta();
                }
            },
            error: () => {
                this.transactions = [];
                this.transactionDS.data = [];
                this.transactionPA = new DefaultPageMeta();
            }
        });
    }

    nextPage(event: PageEvent) {
        this.transactionPA.page = event.pageIndex + 1;
        this.transactionPA.per_page = event.pageSize;
        this.onSearch();
    }

    resolveClass(code: number) {
        if ([200, 201, 202, 301, 302].includes(code)) {
            return "allow";
        }
        if ([404, 401].includes(code)) {
            return "warn";
        }
        return "deny";
    }

    onShowRAW(trn: TransactionLog) {
        this.confirmDialog.open(TransactionRAWDialogComponent, {
            data: trn,
            width: '780px',
            maxWidth: '90vw',
        });
    }

    onShowRuleDetails(rule_code: number) {
        this.ruleService.get_by_code(rule_code).subscribe(data => {
            this.confirmDialog.open(RuleDetailsDialogComponent, {
                data: data,
                width: '780px',
                maxWidth: '90vw',
            });
        });
    }

    ngAfterViewInit(): void {
        this.responsive.observe([Breakpoints.Small])
            .subscribe(result => {
                if (this.chart) {
                    if (result.breakpoints[Breakpoints.Small]) {
                        this.chart.options.aspectRatio = 2.5;
                    }
                    this.chart.update();
                }
            });
    }

    openFilterDialog(): void {
        const dialogRef = this.confirmDialog.open(TransactionFilterDialogComponent, {
            width: '620px',
            maxWidth: '95vw',
        });

        dialogRef.afterClosed().subscribe((result: string | undefined) => {
            if (result) {
                this.addFilterString(result);
            }
        });
    }

    addFilterString(filterStr: string): void {
        try {
            const filter = JSON.parse(filterStr);
            if (typeof filter !== 'object' || filter === null) {
                throw new Error('Filter must be a JSON object');
            }
            if (this.form.value.filters == null) {
                this.form.value.filters = [];
            }
            const existingFilters = this.form.value.filters.map((f: string) => {
                try {
                    return JSON.parse(f);
                } catch {
                    return {};
                }
            });
            const newKeys = Object.keys(filter);

            for (const existingFilter of existingFilters) {
                const existingKeys = Object.keys(existingFilter);
                const duplicates = newKeys.filter((key) => existingKeys.includes(key));
                if (duplicates.length > 0) {
                    throw new Error(`Filter already exists for: ${duplicates.join(', ')}`);
                }
            }

            this.form.value.filters.push(JSON.stringify(filter));
            this.onSearch();
        } catch (error: unknown) {
            const errorMessage =
                error instanceof Error
                    ? error.message
                    : 'Invalid filter format. Please enter a valid JSON object.';
            this.snackBar.open(errorMessage, 'Close', {
                duration: 5000,
                horizontalPosition: 'center',
                verticalPosition: 'bottom',
            });
        }
    }

    onAddFilter(): void {
        if (!this.input_regex.trim()) {
            return;
        }
        this.addFilterString(this.input_regex);
        this.input_regex = '';
    }

    onRemoveFilter(keyword: any): void {
        if (this.form.value.filters != null) {
            const index = this.form.value.filters.indexOf(keyword);
            if (index >= 0) {
                this.form.value.filters.splice(index, 1);
                this.onSearch();
            }
        }
    }

    onClearAllFilters(): void {
        this.form.get('filters')?.setValue([]);
        if (this.form.value.filters) {
            this.form.value.filters = [];
        }
        this.onSearch();
    }

    formatFilterChip(filterStr: string): string {
        try {
            const parsed = JSON.parse(filterStr);
            const entries = Object.entries(parsed);
            if (entries.length === 0) return filterStr;
            return entries.map(([k, v]) => `${k} = ${v}`).join(' & ');
        } catch {
            return filterStr;
        }
    }

    onDateTimeConfirm(event: any, form_field: string) {
        this.form.get(form_field)?.setValue(event.toDate());
    }
}