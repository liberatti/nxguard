import { Component, OnInit, AfterViewInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import moment from 'moment';
import Chart from 'chart.js/auto';

import { HealthService } from '../../services/config.service';
import { RouteService } from '../../services/route.service';
import { ServiceService } from '../../services/service.service';
import { TransactionService } from '../../services/transaction.service';
import { UpstreamService } from '../../services/upstream.service';
import { EngineNode, Health } from '../../models/config';
import { TransactionLog } from '../../models/transaction';
import { DateFormatPipe } from '../../pipes/date_format.pipe';
import { ByteFormatPipe } from '../../pipes/format_bytes.pipe';
import { TranslatePipe } from '@ngx-translate/core';
import { NodeDetailsDialogComponent } from '../../components/node-details-dialog/node-details-dialog.component';
import { TransactionRAWDialogComponent } from '../../components/transaction-raw-dialog/transaction-raw-dialog.component';

@Component({
    selector: 'app-dashboard-home',
    standalone: true,
    imports: [
        CommonModule,
        RouterModule,
        FormsModule,
        ReactiveFormsModule,
        MatFormFieldModule,
        MatSelectModule,
        MatIconModule,
        MatButtonModule,
        MatCardModule,
        MatTooltipModule,
        DateFormatPipe,
        ByteFormatPipe,
        TranslatePipe,
    ],
    templateUrl: './dashboard-home.component.html',
    styleUrl: './dashboard-home.component.css',
})
export class DashboardHomeComponent implements OnInit, AfterViewInit, OnDestroy {
    health: Health = {} as Health;
    totalThreats: number = 0;
    totalUpstreams: number = 0;
    totalRequests: number = 0;
    blockedRequests: number = 0;
    warnRequests: number = 0;
    totalRoutes: number = 0;
    threatLogs: TransactionLog[] = [];
    criticalIncidents: number = 0;
    highIncidents: number = 0;
    peakTpm: number = 0;
    avgTpm: number = 0;
    totalBytesIn: number = 0;
    totalBytesOut: number = 0;
    bandwidthChart: any;
    requestsChart: any;

    refreshIntervalSeconds: number = 10;
    private autoRefreshTimer: any = null;

    constructor(
        private detailsDialog: MatDialog,
        private healthService: HealthService,
        private routeService: RouteService,
        private serviceService: ServiceService,
        private transactionService: TransactionService,
        private upstreamService: UpstreamService,
        private cdr: ChangeDetectorRef
    ) { }

    get systemStatus(): string {
        if (this.health && this.health.nodes && this.health.nodes.length > 0) {
            const hasError = this.health.nodes.some(
                (n: EngineNode) => n.status === 'ERROR'
            );
            return hasError ? 'DEGRADED' : 'HEALTHY';
        }
        return 'HEALTHY';
    }

    get activeNodesCount(): number {
        return this.health && this.health.nodes ? this.health.nodes.length : 1;
    }

    ngOnInit(): void {
        this.refresh();
        this.startAutoRefresh();
    }

    ngAfterViewInit(): void {
        setTimeout(() => {
            this.loadTrafficChart();
        }, 100);
    }

    ngOnDestroy(): void {
        this.stopAutoRefresh();
        if (this.bandwidthChart) {
            this.bandwidthChart.destroy();
        }
        if (this.requestsChart) {
            this.requestsChart.destroy();
        }
    }

    onRefreshIntervalChange(seconds: number): void {
        this.refreshIntervalSeconds = seconds;
        this.stopAutoRefresh();
        if (this.refreshIntervalSeconds > 0) {
            this.startAutoRefresh();
        }
    }

    startAutoRefresh(): void {
        this.stopAutoRefresh();
        if (this.refreshIntervalSeconds > 0) {
            this.autoRefreshTimer = setInterval(() => {
                this.refresh();
            }, this.refreshIntervalSeconds * 1000);
        }
    }

    stopAutoRefresh(): void {
        if (this.autoRefreshTimer) {
            clearInterval(this.autoRefreshTimer);
            this.autoRefreshTimer = null;
        }
    }

    refresh(): void {
        this.loadHealth();
        this.loadUpstreams();
        this.loadProtectedAssets();
        this.loadRequestStats();
        this.loadThreatLogs();
        this.loadTrafficChart();
    }

    loadUpstreams(): void {
        this.upstreamService.get().subscribe({
            next: (res: any) => {
                this.totalUpstreams =
                    res?.metadata?.total_elements ??
                    (Array.isArray(res?.data)
                        ? res.data.length
                        : Array.isArray(res)
                            ? res.length
                            : 0);
                this.cdr.markForCheck();
            },
            error: () => {
                this.totalUpstreams = 0;
                this.cdr.markForCheck();
            },
        });
    }

    loadHealth(): void {
        this.healthService.check().subscribe({
            next: (data) => {
                this.health = data;
                this.cdr.markForCheck();
            },
            error: () => {
                this.health = {} as Health;
                this.cdr.markForCheck();
            },
        });
    }

    loadProtectedAssets(): void {
        this.routeService.get().subscribe({
            next: (res: any) => {
                const total =
                    res?.metadata?.total_elements ??
                    (Array.isArray(res?.data)
                        ? res.data.length
                        : Array.isArray(res)
                            ? res.length
                            : 0);
                if (total > 0) {
                    this.totalRoutes = total;
                    this.cdr.markForCheck();
                } else {
                    this.loadRoutesFromServices();
                }
            },
            error: () => {
                this.loadRoutesFromServices();
            },
        });
    }

    private loadRoutesFromServices(): void {
        this.serviceService.get().subscribe({
            next: (res: any) => {
                const services = res?.data || (Array.isArray(res) ? res : []);
                let count = 0;
                for (const svc of services) {
                    if (svc.routes && Array.isArray(svc.routes)) {
                        count += svc.routes.length;
                    }
                }
                this.totalRoutes = count;
                this.cdr.markForCheck();
            },
            error: () => {
                this.totalRoutes = 0;
                this.cdr.markForCheck();
            },
        });
    }

    loadRequestStats(): void {
        const start = moment().subtract(24, 'hours').toDate();
        const end = moment().toDate();

        this.transactionService
            .search({ start, end, filters: [] }, { page: 1, per_page: 1 } as any)
            .subscribe({
                next: (res) => {
                    this.totalRequests = res?.metadata?.total_elements || 0;
                    this.cdr.markForCheck();
                },
                error: () => {
                    this.totalRequests = 0;
                    this.cdr.markForCheck();
                },
            });

        this.transactionService
            .search(
                { start, end, filters: ['{"action": "DENY"}'] },
                { page: 1, per_page: 1 } as any
            )
            .subscribe({
                next: (res) => {
                    this.blockedRequests = res?.metadata?.total_elements || 0;
                    this.totalThreats = this.blockedRequests;
                    this.cdr.markForCheck();
                },
                error: () => {
                    this.blockedRequests = 0;
                    this.totalThreats = 0;
                    this.cdr.markForCheck();
                },
            });

        this.transactionService
            .search(
                { start, end, filters: ['{"action": "WARN"}'] },
                { page: 1, per_page: 1 } as any
            )
            .subscribe({
                next: (res) => {
                    this.warnRequests = res?.metadata?.total_elements || 0;
                    this.cdr.markForCheck();
                },
                error: () => {
                    this.warnRequests = 0;
                    this.cdr.markForCheck();
                },
            });
    }

    loadThreatLogs(): void {
        this.transactionService
            .search(
                {
                    start: moment().subtract(24, 'hours').toDate(),
                    end: moment().toDate(),
                    filters: [],
                },
                { page: 1, per_page: 8 } as any
            )
            .subscribe({
                next: (res) => {
                    const list = res?.data || [];
                    this.threatLogs = list;
                    this.criticalIncidents = list.filter(
                        (t: TransactionLog) => t.action === 'DENY'
                    ).length;
                    this.highIncidents = list.filter(
                        (t: TransactionLog) =>
                            t.action === 'WARN' || t.action === 'REJECTED'
                    ).length;
                    this.cdr.markForCheck();
                },
                error: () => {
                    this.threatLogs = [];
                    this.criticalIncidents = 0;
                    this.highIncidents = 0;
                    this.cdr.markForCheck();
                },
            });
    }

    loadTrafficChart(): void {
        this.transactionService
            .getTpm({
                start: moment().subtract(24, 'hours').toDate(),
                end: moment().toDate(),
                filters: [],
            })
            .subscribe({
                next: (data) => {
                    this.renderChart(data || []);
                },
                error: () => {
                    this.renderChart([]);
                },
            });
    }

    renderChart(data: any[]): void {
        const labels = data.map((d) => moment(d.logtime).format('HH:mm'));
        const counts = data.map((d) => d.count || 0);
        const bytesIn = data.map((d) => d.bytes_in || 0);
        const bytesOut = data.map((d) => d.bytes_out || 0);

        if (counts.length > 0) {
            this.peakTpm = Math.max(...counts);
            const sum = counts.reduce((a, b) => a + b, 0);
            this.avgTpm = Math.round(sum / counts.length);
        } else {
            this.peakTpm = 0;
            this.avgTpm = 0;
        }

        this.totalBytesIn = bytesIn.reduce((a, b) => a + b, 0);
        this.totalBytesOut = bytesOut.reduce((a, b) => a + b, 0);

        const formatBytes = (bytes: number, decimals: number = 1): string => {
            if (!bytes || bytes === 0) return '0 B';
            const k = 1024;
            const dm = decimals < 0 ? 0 : decimals;
            const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
        };

        const defaultLabels = ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00'];
        const defaultZeros = [0, 0, 0, 0, 0, 0, 0];
        const chartLabels = labels.length > 0 ? labels : defaultLabels;

        // 1. Render Bandwidth Chart
        if (this.bandwidthChart) {
            this.bandwidthChart.destroy();
        }
        const canvasBandwidth = document.getElementById(
            'dashboard-bandwidth-chart'
        ) as HTMLCanvasElement;
        if (canvasBandwidth) {
            const ctxB = canvasBandwidth.getContext('2d');
            if (ctxB) {
                const gradientIn = ctxB.createLinearGradient(0, 0, 0, 180);
                gradientIn.addColorStop(0, 'rgba(2, 132, 199, 0.28)');
                gradientIn.addColorStop(0.7, 'rgba(2, 132, 199, 0.05)');
                gradientIn.addColorStop(1, 'rgba(2, 132, 199, 0.0)');

                const gradientOut = ctxB.createLinearGradient(0, 0, 0, 180);
                gradientOut.addColorStop(0, 'rgba(16, 185, 129, 0.28)');
                gradientOut.addColorStop(0.7, 'rgba(16, 185, 129, 0.05)');
                gradientOut.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

                this.bandwidthChart = new Chart(canvasBandwidth, {
                    type: 'line',
                    data: {
                        labels: chartLabels,
                        datasets: [
                            {
                                label: 'Bytes In (Inbound)',
                                data: bytesIn.length > 0 ? bytesIn : defaultZeros,
                                borderColor: '#0284c7',
                                backgroundColor: gradientIn,
                                fill: true,
                                tension: 0.35,
                                borderWidth: 2,
                                pointRadius: 0,
                                pointHoverRadius: 5,
                                pointHoverBackgroundColor: '#0284c7',
                                pointHoverBorderColor: '#ffffff',
                                pointHoverBorderWidth: 2,
                            },
                            {
                                label: 'Bytes Out (Outbound)',
                                data: bytesOut.length > 0 ? bytesOut : defaultZeros,
                                borderColor: '#10b981',
                                backgroundColor: gradientOut,
                                fill: true,
                                tension: 0.35,
                                borderWidth: 2,
                                pointRadius: 0,
                                pointHoverRadius: 5,
                                pointHoverBackgroundColor: '#10b981',
                                pointHoverBorderColor: '#ffffff',
                                pointHoverBorderWidth: 2,
                            },
                        ],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {
                            intersect: false,
                            mode: 'index',
                        },
                        plugins: {
                            datalabels: {
                                display: false,
                            },
                            legend: {
                                display: true,
                                position: 'top',
                                align: 'end',
                                labels: {
                                    boxWidth: 10,
                                    boxHeight: 10,
                                    usePointStyle: true,
                                    pointStyle: 'circle',
                                    color: '#475569',
                                    font: { size: 11, weight: 'bold' },
                                    padding: 10,
                                },
                            },
                            tooltip: {
                                enabled: true,
                                backgroundColor: '#0f172a',
                                titleColor: '#f8fafc',
                                bodyColor: '#e2e8f0',
                                titleFont: { size: 12, weight: 'bold' },
                                bodyFont: { size: 12, weight: 'normal' },
                                padding: 10,
                                cornerRadius: 8,
                                borderColor: 'rgba(255, 255, 255, 0.1)',
                                borderWidth: 1,
                                displayColors: true,
                                boxWidth: 8,
                                boxHeight: 8,
                                usePointStyle: true,
                                callbacks: {
                                    label: (context) => {
                                        const val = context.parsed.y ?? 0;
                                        return ` ${context.dataset.label}: ${formatBytes(val)}`;
                                    },
                                },
                            },
                        },
                        scales: {
                            x: {
                                grid: {
                                    color: 'rgba(0, 0, 0, 0.04)',
                                },
                                ticks: {
                                    color: '#64748b',
                                    font: { size: 10, weight: 500 },
                                    maxTicksLimit: 8,
                                },
                                border: {
                                    display: false,
                                },
                            },
                            y: {
                                beginAtZero: true,
                                grid: {
                                    color: 'rgba(0, 0, 0, 0.04)',
                                },
                                ticks: {
                                    color: '#64748b',
                                    font: { size: 10, weight: 500 },
                                    callback: (val: any) => formatBytes(Number(val)),
                                },
                                border: {
                                    display: false,
                                },
                            },
                        },
                    },
                });
            }
        }

        // 2. Render Requests Chart
        if (this.requestsChart) {
            this.requestsChart.destroy();
        }
        const canvasRequests = document.getElementById(
            'dashboard-requests-chart'
        ) as HTMLCanvasElement;
        if (canvasRequests) {
            const ctxR = canvasRequests.getContext('2d');
            if (ctxR) {
                const gradientReq = ctxR.createLinearGradient(0, 0, 0, 180);
                gradientReq.addColorStop(0, 'rgba(139, 92, 246, 0.28)');
                gradientReq.addColorStop(0.7, 'rgba(139, 92, 246, 0.05)');
                gradientReq.addColorStop(1, 'rgba(139, 92, 246, 0.0)');

                this.requestsChart = new Chart(canvasRequests, {
                    type: 'line',
                    data: {
                        labels: chartLabels,
                        datasets: [
                            {
                                label: 'Requests / min',
                                data: counts.length > 0 ? counts : defaultZeros,
                                borderColor: '#8b5cf6',
                                backgroundColor: gradientReq,
                                fill: true,
                                tension: 0.35,
                                borderWidth: 2,
                                pointRadius: 0,
                                pointHoverRadius: 5,
                                pointHoverBackgroundColor: '#8b5cf6',
                                pointHoverBorderColor: '#ffffff',
                                pointHoverBorderWidth: 2,
                            },
                        ],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {
                            intersect: false,
                            mode: 'index',
                        },
                        plugins: {
                            datalabels: {
                                display: false,
                            },
                            legend: {
                                display: false,
                            },
                            tooltip: {
                                enabled: true,
                                backgroundColor: '#0f172a',
                                titleColor: '#f8fafc',
                                bodyColor: '#e2e8f0',
                                titleFont: { size: 12, weight: 'bold' },
                                bodyFont: { size: 12, weight: 'normal' },
                                padding: 10,
                                cornerRadius: 8,
                                borderColor: 'rgba(255, 255, 255, 0.1)',
                                borderWidth: 1,
                                displayColors: false,
                                callbacks: {
                                    label: (context) => {
                                        const val = context.parsed.y ?? 0;
                                        return ` Requests: ${val} req/m`;
                                    },
                                },
                            },
                        },
                        scales: {
                            x: {
                                grid: {
                                    color: 'rgba(0, 0, 0, 0.04)',
                                },
                                ticks: {
                                    color: '#64748b',
                                    font: { size: 10, weight: 500 },
                                    maxTicksLimit: 8,
                                },
                                border: {
                                    display: false,
                                },
                            },
                            y: {
                                beginAtZero: true,
                                grid: {
                                    color: 'rgba(0, 0, 0, 0.04)',
                                },
                                ticks: {
                                    color: '#64748b',
                                    font: { size: 10, weight: 500 },
                                    precision: 0,
                                },
                                border: {
                                    display: false,
                                },
                            },
                        },
                    },
                });
            }
        }
    }

    show_details(nodeData: EngineNode): void {
        this.detailsDialog.open(NodeDetailsDialogComponent, {
            data: nodeData,
            width: '450px',
        });
    }

    showRawLog(log: TransactionLog): void {
        this.detailsDialog.open(TransactionRAWDialogComponent, {
            data: log,
        });
    }
}
