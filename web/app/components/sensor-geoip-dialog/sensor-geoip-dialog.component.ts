import { Component, Inject, OnInit } from '@angular/core';
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
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { TranslatePipe, TranslateService } from '@ngx-translate/core';
import { GeoCountryService, RegionGroup, CountryInfo } from '../../services/geo-country.service';
import { SensorService } from '../../services/sensor.service';
import { NotificationService } from '../../services/notification.service';
import { Sensor } from '../../models/sensor';

export interface SensorGeoipDialogData {
    sensorName?: string;
    geo_codes?: string[];
    sensor?: Sensor;
    sensorId?: string | number;
    editable?: boolean;
}

export interface SensorGeoipDialogResult {
    updated: boolean;
    geo_codes: string[];
    sensor?: Sensor;
}

@Component({
    selector: 'app-sensor-geoip-dialog',
    templateUrl: './sensor-geoip-dialog.component.html',
    styleUrl: './sensor-geoip-dialog.component.css',
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
        MatSelectModule,
        MatTooltipModule,
        MatProgressSpinnerModule,
        TranslatePipe
    ]
})
export class SensorGeoipDialogComponent implements OnInit {
    searchQuery: string = '';
    editableGeoCodes: string[] = [];
    allCountries: CountryInfo[] = [];
    selectedCountryToAdd: string = '';
    isSaving: boolean = false;

    constructor(
        @Inject(MAT_DIALOG_DATA) public data: SensorGeoipDialogData,
        public dialogRef: MatDialogRef<SensorGeoipDialogComponent, SensorGeoipDialogResult>,
        private geoCountryService: GeoCountryService,
        private sensorService: SensorService,
        private notificationService: NotificationService,
        private translate: TranslateService
    ) {}

    ngOnInit(): void {
        this.editableGeoCodes = (this.data?.geo_codes || this.data?.sensor?.security?.geo_codes || []).slice();
        this.allCountries = this.geoCountryService.getAllCountries();
    }

    get isEditable(): boolean {
        return !!this.data?.editable;
    }

    get totalCount(): number {
        return this.editableGeoCodes.length;
    }

    get regionGroups(): RegionGroup[] {
        return this.geoCountryService.groupCountriesByRegion(
            this.editableGeoCodes,
            this.searchQuery
        );
    }

    get filteredCount(): number {
        return this.regionGroups.reduce((acc, g) => acc + g.countries.length, 0);
    }

    get availableCountries(): CountryInfo[] {
        const active = new Set(this.editableGeoCodes);
        return this.allCountries.filter(c => !active.has(c.code));
    }

    addCountry(code: string): void {
        if (!code) return;
        if (!this.editableGeoCodes.includes(code)) {
            this.editableGeoCodes.push(code);
        }
        this.selectedCountryToAdd = '';
    }

    removeCountry(code: string, event?: Event): void {
        if (event) {
            event.stopPropagation();
        }
        this.editableGeoCodes = this.editableGeoCodes.filter(c => c !== code);
    }

    clearAll(): void {
        this.editableGeoCodes = [];
    }

    clearSearch(): void {
        this.searchQuery = '';
    }

    onClose(): void {
        this.dialogRef.close();
    }

    onSave(): void {
        const updatedCodes = [...this.editableGeoCodes];
        const sensorId = this.data?.sensorId || this.data?.sensor?._id;

        if (sensorId) {
            this.isSaving = true;
            const updatePayload = (base: Sensor) => {
                const updatedSensor: Sensor = {
                    ...base,
                    security: {
                        ...(base.security || { reputation: [], trusted: [] }),
                        geo_codes: updatedCodes,
                        geo_codes_count: updatedCodes.length
                    }
                };
                this.sensorService.update(String(sensorId), updatedSensor).subscribe({
                    next: (saved) => {
                        this.isSaving = false;
                        this.translate.stream('SENSOR.SAVED_SUCCESS').subscribe(msg => this.notificationService.openSnackBar(msg));
                        this.dialogRef.close({
                            updated: true,
                            geo_codes: updatedCodes,
                            sensor: saved || updatedSensor
                        });
                    },
                    error: () => {
                        this.isSaving = false;
                        this.notificationService.openSnackBar('Error updating sensor');
                    }
                });
            };

            if (this.data?.sensor && this.data.sensor.name) {
                updatePayload(this.data.sensor);
            } else {
                this.sensorService.getById(String(sensorId)).subscribe({
                    next: (fetched) => updatePayload(fetched),
                    error: () => updatePayload({ _id: sensorId, name: this.data?.sensorName || '' } as Sensor)
                });
            }
        } else {
            this.dialogRef.close({
                updated: true,
                geo_codes: updatedCodes
            });
        }
    }
}
