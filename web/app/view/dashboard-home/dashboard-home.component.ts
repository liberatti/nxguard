import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog } from '@angular/material/dialog';
import moment from 'moment';
import Chart from 'chart.js/auto';

import { HealthService } from '../../services/config.service';
import { RouteService } from '../../services/route.service';
import { TransactionService } from '../../services/transaction.service';
import { EngineNode, Health } from '../../models/config';
import { TransactionLog } from '../../models/transaction';
import { DateFormatPipe } from '../../pipes/date_format.pipe';
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
        MatIconModule,
        MatButtonModule,
        MatCardModule,
        MatTooltipModule,
        DateFormatPipe,
    ],
    templateUrl: './dashboard-home.component.html',
    styleUrl: './dashboard-home.component.css',
})
export class DashboardHomeComponent implements OnInit, OnDestroy {
    health: Health = {} as Health;
    totalThreats: number = 0;
    totalRoutes: number = 0;
    threatLogs: TransactionLog[] = [];
    criticalIncidents: number = 0;
    highIncidents: number = 0;
    peakTpm: number = 0;
    avgTpm: number = 0;
    chart: any;

    constructor(
        private detailsDialog: MatDialog,
        private healthService: HealthService,
        private routeService: RouteService,
        private transactionService: TransactionService
    ) {}

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
        this.loadHealth();
        this.loadProtectedAssets();
        this.loadTotalThreats();
        this.loadThreatLogs();
        this.loadTrafficChart();
    }

    ngOnDestroy(): void {
        if (this.chart) {
            this.chart.destroy();
        }
    }

    loadHealth(): void {
        this.healthService.check().subscribe({
            next: (data) => {
                this.health = data;
            },
            error: () => {
                this.health = {} as Health;
            },
        });
    }

    loadProtectedAssets(): void {
        this.routeService.get({ page: 1, per_page: 1 } as any).subscribe({
            next: (res) => {
                this.totalRoutes =
                    res?.metadata?.total_elements ??
                    (Array.isArray(res?.data) ? res.data.length : 0);
            },
            error: () => {
                this.totalRoutes = 0;
            },
        });
    }

    loadTotalThreats(): void {
        this.transactionService
            .search(
                {
                    start: moment().subtract(24, 'hours').toDate(),
                    end: moment().toDate(),
                    filters: ['{"action": "DENY"}'],
                },
                { page: 1, per_page: 1 } as any
            )
            .subscribe({
                next: (res) => {
                    this.totalThreats = res?.metadata?.total_elements || 0;
                },
                error: () => {
                    this.totalThreats = 0;
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
                },
                error: () => {
                    this.threatLogs = [];
                    this.criticalIncidents = 0;
                    this.highIncidents = 0;
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
        if (this.chart) {
            this.chart.destroy();
        }
        const canvas = document.getElementById(
            'dashboard-traffic-chart'
        ) as HTMLCanvasElement;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const labels = data.map((d) => moment(d.logtime).format('HH:mm'));
        const counts = data.map((d) => d.count);

        if (counts.length > 0) {
            this.peakTpm = Math.max(...counts);
            const sum = counts.reduce((a, b) => a + b, 0);
            this.avgTpm = Math.round(sum / counts.length);
        } else {
            this.peakTpm = 0;
            this.avgTpm = 0;
        }

        const gradient = ctx.createLinearGradient(0, 0, 0, 260);
        gradient.addColorStop(0, 'rgba(2, 132, 199, 0.25)');
        gradient.addColorStop(0.6, 'rgba(2, 132, 199, 0.05)');
        gradient.addColorStop(1, 'rgba(2, 132, 199, 0.0)');

        this.chart = new Chart(canvas, {
            type: 'line',
            data: {
                labels:
                    labels.length > 0
                        ? labels
                        : ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00'],
                datasets: [
                    {
                        label: 'Requests / min',
                        data: counts.length > 0 ? counts : [0, 0, 0, 0, 0, 0, 0],
                        borderColor: '#0284c7',
                        backgroundColor: gradient,
                        fill: true,
                        tension: 0.35,
                        borderWidth: 2.5,
                        pointRadius: 0,
                        pointHoverRadius: 6,
                        pointHoverBackgroundColor: '#0284c7',
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
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: '#0f172a',
                        titleColor: '#f8fafc',
                        bodyColor: '#38bdf8',
                        titleFont: { size: 12, weight: 'bold' },
                        bodyFont: { size: 14, weight: 'bold' },
                        padding: 12,
                        cornerRadius: 8,
                        borderColor: 'rgba(2, 132, 199, 0.4)',
                        borderWidth: 1,
                        displayColors: false,
                        callbacks: {
                            label: (context) => `${context.parsed.y} req / min`,
                        },
                    },
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)',
                        },
                        ticks: {
                            color: '#64748b',
                            font: { size: 11, weight: 500 },
                            maxTicksLimit: 8,
                        },
                        border: {
                            display: false,
                        },
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)',
                        },
                        ticks: {
                            color: '#64748b',
                            font: { size: 11, weight: 500 },
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
