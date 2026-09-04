import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialogActions, MatDialogContent, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { saveAs } from 'file-saver';
import { MatTabChangeEvent, MatTabsModule } from '@angular/material/tabs';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { TranslatePipe } from '@ngx-translate/core';
import { RouterModule } from '@angular/router';
import { NotificationService } from "../../services/notification.service";
import { environment } from 'environments/environment';
import { ConfigService } from "../../services/config.service";


import { MatTooltipModule } from '@angular/material/tooltip';

@Component({
    selector: 'app-about-dialog',
    templateUrl: './about-dialog.component.html',
    styleUrl: './about-dialog.component.css',
    standalone: true,
    imports: [
        CommonModule, RouterModule,
        MatFormFieldModule,
        MatInputModule,
        FormsModule, MatCardModule,
        MatButtonModule,
        MatDialogContent,
        MatDialogActions,
        MatTabsModule, MatIconModule, MatTooltipModule, TranslatePipe
    ],
})

export class AboutDialogComponent {
    selectedFile: File | null = null;
    currentTab: number = 0;
    restoreReady: boolean = true;
    version: string = environment.version;
    constructor(
        public dialogRef: MatDialogRef<AboutDialogComponent>,
        private configService: ConfigService,
        private notificationService: NotificationService,
    ) {
    }

    onFileSelected(event: any): void {
        this.selectedFile = event.target.files[0];
        if (this.selectedFile) {
            const isJson = this.selectedFile.name.toLowerCase().endsWith('.json') || this.selectedFile.type === 'application/json';
            if (!isJson) {
                this.notificationService.openSnackBar('Only JSON files are allowed');
                this.selectedFile = null;
            }
        }
    }

    onSubmit(): void {
        if (!this.selectedFile) {
            this.notificationService.openSnackBar('Please select a JSON file to upload');
            return;
        }
        let formData = new FormData();
        formData.append('file', this.selectedFile, this.selectedFile.name);
        this.restoreReady = false;

        this.configService.uploadConfig(formData).subscribe({
            next: (data) => {
                this.restoreReady = true;
                this.notificationService.openSnackBar('Config restored successfully');
                this.dialogRef.close(true);
            },
            error: (err) => {
                this.restoreReady = true;
                this.notificationService.openSnackBar('Failed to restore');
            }
        });
    }

    onDismiss(): void {
        this.dialogRef.close(false);
    }

    downloadConfig(): void {
        this.configService.downloadConfig().subscribe((resultBlob) => {
            const blob = new Blob([resultBlob], { type: 'application/json' });
            saveAs(blob, 'init-data.json');
        });
    }

    onTabChanged(event: MatTabChangeEvent) {
        this.currentTab = event.index;
    }

    clearSelectedFile(event?: Event): void {
        if (event) {
            event.stopPropagation();
            event.preventDefault();
        }
        this.selectedFile = null;
    }

    formatFileSize(bytes?: number): string {
        if (!bytes) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}