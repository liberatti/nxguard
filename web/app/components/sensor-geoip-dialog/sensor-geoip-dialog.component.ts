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
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { TranslatePipe, TranslateService } from '@ngx-translate/core';
import { GeoCountryService, ContinentRegion, CountryInfo } from '../../services/geo-country.service';
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
        MatCheckboxModule,
        MatSlideToggleModule,
        MatTooltipModule,
        MatProgressSpinnerModule,
        TranslatePipe
    ]
})
export class SensorGeoipDialogComponent implements OnInit {
    searchQuery: string = '';
    isBlockingActive: boolean = true;
    selectedCountryCodes: Set<string> = new Set<string>();
    expandedContinents: Record<string, boolean> = {
        asia: true // Default open or active as in the screenshot
    };
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
        const rawCodes = this.data?.geo_codes || this.data?.sensor?.security?.geo_codes || [];
        this.selectedCountryCodes = new Set<string>(rawCodes.map(c => (c || '').trim().toUpperCase()));
        this.isBlockingActive = this.selectedCountryCodes.size > 0 || this.data?.editable !== false;
    }

    get isEditable(): boolean {
        return this.data?.editable !== false;
    }

    get continents(): ContinentRegion[] {
        return this.geoCountryService.getContinentRegions(this.searchQuery);
    }

    get totalSelectedCount(): number {
        return this.selectedCountryCodes.size;
    }

    isContinentExpanded(id: string): boolean {
        if (this.searchQuery && this.searchQuery.trim().length > 0) {
            return true;
        }
        return !!this.expandedContinents[id];
    }

    toggleContinent(id: string, event?: Event): void {
        if (event) {
            event.stopPropagation();
        }
        this.expandedContinents[id] = !this.expandedContinents[id];
    }

    isContinentAllSelected(continent: ContinentRegion): boolean {
        if (!continent.countries.length) return false;
        return continent.countries.every(c => this.selectedCountryCodes.has(c.code.toUpperCase()));
    }

    isContinentPartiallySelected(continent: ContinentRegion): boolean {
        const selected = this.getContinentSelectedCount(continent);
        return selected > 0 && selected < continent.countries.length;
    }

    getContinentSelectedCount(continent: ContinentRegion): number {
        return continent.countries.filter(c => this.selectedCountryCodes.has(c.code.toUpperCase())).length;
    }

    onContinentCheckboxChange(continent: ContinentRegion, checked: boolean, event?: unknown): void {
        if (event && typeof event === 'object' && 'stopPropagation' in event) {
            (event as Event).stopPropagation();
        }
        if (checked) {
            continent.countries.forEach(c => this.selectedCountryCodes.add(c.code.toUpperCase()));
        } else {
            continent.countries.forEach(c => this.selectedCountryCodes.delete(c.code.toUpperCase()));
        }
    }

    selectAllInContinent(continent: ContinentRegion, event?: Event): void {
        if (event) {
            event.stopPropagation();
        }
        continent.countries.forEach(c => this.selectedCountryCodes.add(c.code.toUpperCase()));
    }

    deselectAllInContinent(continent: ContinentRegion, event?: Event): void {
        if (event) {
            event.stopPropagation();
        }
        continent.countries.forEach(c => this.selectedCountryCodes.delete(c.code.toUpperCase()));
    }

    isCountrySelected(code: string): boolean {
        return this.selectedCountryCodes.has((code || '').toUpperCase());
    }

    toggleCountry(code: string, checked?: boolean, event?: unknown): void {
        if (event && typeof event === 'object' && 'stopPropagation' in event) {
            (event as Event).stopPropagation();
        }
        const upper = (code || '').toUpperCase();
        if (checked !== undefined) {
            if (checked) {
                this.selectedCountryCodes.add(upper);
            } else {
                this.selectedCountryCodes.delete(upper);
            }
        } else {
            if (this.selectedCountryCodes.has(upper)) {
                this.selectedCountryCodes.delete(upper);
            } else {
                this.selectedCountryCodes.add(upper);
            }
        }
    }

    clearSearch(): void {
        this.searchQuery = '';
    }

    onClose(): void {
        this.dialogRef.close();
    }

    onSave(): void {
        const updatedCodes = this.isBlockingActive ? Array.from(this.selectedCountryCodes) : [];
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
