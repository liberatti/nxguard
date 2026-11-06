import {Component, Inject, OnInit, ChangeDetectorRef} from '@angular/core';
import {CommonModule} from '@angular/common';
import {
    MAT_DIALOG_DATA,
    MatDialogActions,
    MatDialogContent,
    MatDialogRef,
    MatDialogTitle
} from '@angular/material/dialog';
import {MatButtonModule} from '@angular/material/button';
import {MatIconModule} from '@angular/material/icon';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import {MatTooltipModule} from '@angular/material/tooltip';
import {TranslatePipe} from '@ngx-translate/core';
import {Upstream, UpstreamHealthStatus} from '../../models/upstream';
import {UpstreamService} from '../../services/upstream.service';

export interface UpstreamStateRecord {
    _id?: number | string;
    node_id: string;
    upstream_id: number;
    healthy: UpstreamHealthStatus | boolean | string;
    last_check: string;
    targets: Array<{
        host?: string;
        port?: number;
        endpoint: string;
        healthy: boolean;
        latency_ms?: number;
        error?: string;
    }>;
}

@Component({
    selector: 'app-upstream-states-dialog',
    templateUrl: './upstream-states-dialog.component.html',
    styleUrls: ['./upstream-states-dialog.component.css'],
    standalone: true,
    imports: [
        CommonModule,
        MatDialogTitle,
        MatDialogContent,
        MatDialogActions,
        MatButtonModule,
        MatIconModule,
        MatProgressSpinnerModule,
        MatTooltipModule,
        TranslatePipe
    ]
})
export class UpstreamStatesDialogComponent implements OnInit {
    states: UpstreamStateRecord[] = [];
    loading: boolean = true;

    constructor(
        public dialogRef: MatDialogRef<UpstreamStatesDialogComponent>,
        @Inject(MAT_DIALOG_DATA) public data: { upstream: Upstream },
        private upstreamService: UpstreamService,
        private cdr: ChangeDetectorRef
    ) {}

    ngOnInit(): void {
        this.loadStates();
    }

    loadStates(): void {
        this.loading = true;
        const upstreamId = this.data?.upstream?._id;
        if (!upstreamId) {
            this.states = [];
            this.loading = false;
            this.cdr.detectChanges();
            return;
        }

        this.upstreamService.getStates(upstreamId).subscribe({
            next: (res: any) => {
                const raw = res?.data !== undefined ? res.data : res;
                this.states = Array.isArray(raw) ? raw : [];
                this.loading = false;
                this.cdr.detectChanges();
            },
            error: () => {
                this.states = [];
                this.loading = false;
                this.cdr.detectChanges();
            }
        });
    }

    getUpstreamStatusKey(): string {
        const h = this.data?.upstream?.healthy;
        if (h === 'healthy') return 'UPSTREAM.STATES.HEALTHY';
        if (h === 'partially_healthy') return 'UPSTREAM.STATES.PARTIALLY_HEALTHY';
        if (h === 'unhealthy') return 'UPSTREAM.STATES.UNHEALTHY';
        return 'UPSTREAM.STATES.INVALID';
    }

    getNodeStatusKey(h: any): string {
        if (h === true || h === 'healthy') return 'UPSTREAM.STATES.HEALTHY';
        if (h === 'partially_healthy') return 'UPSTREAM.STATES.PARTIALLY_HEALTHY';
        if (h === false || h === 'unhealthy') return 'UPSTREAM.STATES.UNHEALTHY';
        return 'UPSTREAM.STATES.INVALID';
    }

    isNodeHealthy(h: any): boolean {
        return h === true || h === 'healthy';
    }

    isNodePartiallyHealthy(h: any): boolean {
        return h === 'partially_healthy';
    }

    isNodeUnhealthy(h: any): boolean {
        return h === false || h === 'unhealthy';
    }

    onClose(): void {
        this.dialogRef.close();
    }
}
