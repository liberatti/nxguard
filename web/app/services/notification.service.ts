import { Injectable } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MultiSnackbarComponent } from 'app/components/multi-snackbar/multi-snackbar.component';
import { APIErrorResponse } from 'app/models/shared';

@Injectable({
    providedIn: 'root'
})
export class NotificationService {

    constructor(private snackBar: MatSnackBar) { }

    public openSnackBar(message: string | string[]) {
        if (Array.isArray(message)) {
            const detailsObj: any = {};
            message.forEach((msg, idx) => {
                const parts = msg.trim().split('on ');
                const fieldName = parts.length > 1 ? parts[1].trim() : `error_${idx + 1}`;
                detailsObj[fieldName] = [msg.trim()];
            });

            this.snackBar.openFromComponent(MultiSnackbarComponent, {
                data: {
                    messages: message,
                    errorData: {
                        code: 400,
                        message: 'Validation Error',
                        details: detailsObj
                    }
                },
                duration: 5000,
                panelClass: 'snackbar-error',
                verticalPosition: 'bottom',
                horizontalPosition: 'center'
            });
        } else {
            this.snackBar.open(message, '', {
                duration: 5000,
                panelClass: 'snackbar-error',
                verticalPosition: 'bottom',
                horizontalPosition: 'center'
            });
        }
    }

    public openErrorSnackBar(error: APIErrorResponse) {
        const title = `[${error.code || 400}] ${error.message || 'Validation Error'}`;
        this.snackBar.openFromComponent(MultiSnackbarComponent, {
            data: { message: title, errorData: error },
            duration: 8000,
            panelClass: 'snackbar-error',
            verticalPosition: 'bottom',
            horizontalPosition: 'center'
        });
    }
}
