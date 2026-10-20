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
import { BypassFeedService, BypassCategoryGroup } from '../../services/bypass-feed.service';
import { FeedService } from '../../services/feed.service';
import { SensorService } from '../../services/sensor.service';
import { NotificationService } from '../../services/notification.service';
import { Sensor } from '../../models/sensor';

export interface SensorBypassDialogData {
    sensorName?: string;
    trusted?: string[];
    sensor?: Sensor;
    sensorId?: string | number;
    editable?: boolean;
    availableFeeds?: string[];
}

export interface SensorBypassDialogResult {
    updated: boolean;
    trusted: string[];
    sensor?: Sensor;
}

@Component({
    selector: 'app-sensor-bypass-dialog',
    templateUrl: './sensor-bypass-dialog.component.html',
    styleUrl: './sensor-bypass-dialog.component.css',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        MatButtonModule,
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
export class SensorBypassDialogComponent implements OnInit {
    searchQuery: string = '';
    isBypassActive: boolean = true;
    selectedFeeds: Set<string> = new Set<string>();
    expandedCategories: Record<string, boolean> = {
        local: true,
        cdn: true,
        crawlers: true,
        monitoring: true,
        trusted: true
    };
    isSaving: boolean = false;
    availableFeedsList: string[] = [];

    constructor(
        @Inject(MAT_DIALOG_DATA) public data: SensorBypassDialogData,
        public dialogRef: MatDialogRef<SensorBypassDialogComponent, SensorBypassDialogResult>,
        private bypassFeedService: BypassFeedService,
        private feedService: FeedService,
        private sensorService: SensorService,
        private notificationService: NotificationService,
        private translate: TranslateService
    ) {}

    ngOnInit(): void {
        const rawFeeds = this.data?.trusted || this.data?.sensor?.security?.trusted || [];
        this.selectedFeeds = new Set<string>(rawFeeds.map(f => (f || '').trim()));
        this.isBypassActive = this.selectedFeeds.size > 0 || this.data?.editable !== false;

        if (this.data?.availableFeeds && this.data.availableFeeds.length > 0) {
            this.availableFeedsList = [...this.data.availableFeeds];
        } else {
            this.feedService.get_by_type('bypass').subscribe({
                next: (feeds: any) => {
                    const list = Array.isArray(feeds) ? feeds : (feeds?.data || []);
                    const names = list.map((f: any) => f.name || f._id).filter(Boolean);
                    this.availableFeedsList = names;
                },
                error: () => {
                    this.availableFeedsList = [];
                }
            });
        }
    }

    get isEditable(): boolean {
        return this.data?.editable !== false;
    }

    get categories(): BypassCategoryGroup[] {
        const combined = Array.from(new Set([...this.availableFeedsList, ...Array.from(this.selectedFeeds)]));
        return this.bypassFeedService.getAllBypassCategories(combined, this.searchQuery);
    }

    get totalSelectedCount(): number {
        return this.selectedFeeds.size;
    }

    isCategoryExpanded(id: string): boolean {
        if (this.searchQuery && this.searchQuery.trim().length > 0) {
            return true;
        }
        return !!this.expandedCategories[id];
    }

    toggleCategory(id: string, event?: Event): void {
        if (event) {
            event.stopPropagation();
        }
        this.expandedCategories[id] = !this.expandedCategories[id];
    }

    isCategoryAllSelected(category: BypassCategoryGroup): boolean {
        if (!category.providers.length) return false;
        return category.providers.every(p => this.selectedFeeds.has(p.name));
    }

    isCategoryPartiallySelected(category: BypassCategoryGroup): boolean {
        const count = this.getCategorySelectedCount(category);
        return count > 0 && count < category.providers.length;
    }

    getCategorySelectedCount(category: BypassCategoryGroup): number {
        return category.providers.filter(p => this.selectedFeeds.has(p.name)).length;
    }

    onCategoryCheckboxChange(category: BypassCategoryGroup, checked: boolean, event?: unknown): void {
        if (event && typeof event === 'object' && 'stopPropagation' in event) {
            (event as Event).stopPropagation();
        }
        if (checked) {
            category.providers.forEach(p => this.selectedFeeds.add(p.name));
        } else {
            category.providers.forEach(p => this.selectedFeeds.delete(p.name));
        }
    }

    selectAllInCategory(category: BypassCategoryGroup, event?: Event): void {
        if (event) {
            event.stopPropagation();
        }
        category.providers.forEach(p => this.selectedFeeds.add(p.name));
    }

    deselectAllInCategory(category: BypassCategoryGroup, event?: Event): void {
        if (event) {
            event.stopPropagation();
        }
        category.providers.forEach(p => this.selectedFeeds.delete(p.name));
    }

    isFeedSelected(feedName: string): boolean {
        return this.selectedFeeds.has(feedName);
    }

    toggleFeed(feedName: string, checked?: boolean, event?: unknown): void {
        if (event && typeof event === 'object' && 'stopPropagation' in event) {
            (event as Event).stopPropagation();
        }
        if (checked !== undefined) {
            if (checked) {
                this.selectedFeeds.add(feedName);
            } else {
                this.selectedFeeds.delete(feedName);
            }
        } else {
            if (this.selectedFeeds.has(feedName)) {
                this.selectedFeeds.delete(feedName);
            } else {
                this.selectedFeeds.add(feedName);
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
        const updatedFeeds = this.isBypassActive ? Array.from(this.selectedFeeds) : [];
        const sensorId = this.data?.sensorId || this.data?.sensor?._id;

        if (sensorId) {
            this.isSaving = true;
            const updatePayload = (base: Sensor) => {
                const updatedSensor: Sensor = {
                    ...base,
                    security: {
                        ...(base.security || { reputation: [], trusted: [] }),
                        trusted: updatedFeeds,
                        trusted_count: updatedFeeds.length
                    }
                };
                this.sensorService.update(String(sensorId), updatedSensor).subscribe({
                    next: (saved) => {
                        this.isSaving = false;
                        this.translate.stream('SENSOR.SAVED_SUCCESS').subscribe(msg => this.notificationService.openSnackBar(msg));
                        this.dialogRef.close({
                            updated: true,
                            trusted: updatedFeeds,
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
                trusted: updatedFeeds
            });
        }
    }
}
