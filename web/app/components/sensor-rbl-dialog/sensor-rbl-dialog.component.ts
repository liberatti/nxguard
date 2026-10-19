import { Component, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import {
    MAT_DIALOG_DATA,
    MatDialogActions,
    MatDialogContent,
    MatDialogRef,
    MatDialogTitle,
} from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatTooltipModule } from '@angular/material/tooltip';
import { TranslatePipe } from '@ngx-translate/core';
import { RblThreatService, ThreatCategoryGroup } from '../../services/rbl-threat.service';

export interface SensorRblDialogData {
    sensorName?: string;
    reputation: string[];
}

@Component({
    selector: 'app-sensor-rbl-dialog',
    templateUrl: './sensor-rbl-dialog.component.html',
    styleUrl: './sensor-rbl-dialog.component.css',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        MatButtonModule,
        MatDialogTitle,
        MatDialogContent,
        MatDialogActions,
        MatIconModule,
        MatFormFieldModule,
        MatInputModule,
        MatTooltipModule,
        TranslatePipe
    ]
})
export class SensorRblDialogComponent {
    searchQuery: string = '';

    constructor(
        @Inject(MAT_DIALOG_DATA) public data: SensorRblDialogData,
        public dialogRef: MatDialogRef<SensorRblDialogComponent>,
        private rblThreatService: RblThreatService
    ) {}

    get totalCount(): number {
        return this.data?.reputation?.length || 0;
    }

    get categoryGroups(): ThreatCategoryGroup[] {
        return this.rblThreatService.groupProvidersByCategory(
            this.data?.reputation || [],
            this.searchQuery
        );
    }

    get filteredCount(): number {
        return this.categoryGroups.reduce((acc, g) => acc + g.providers.length, 0);
    }

    clearSearch(): void {
        this.searchQuery = '';
    }

    onClose(): void {
        this.dialogRef.close();
    }
}
