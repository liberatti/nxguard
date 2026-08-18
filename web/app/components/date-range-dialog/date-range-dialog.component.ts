import { Component, Inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormControl, FormGroup, Validators } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatMomentDateModule } from '@angular/material-moment-adapter';
import { TranslatePipe } from '@ngx-translate/core';
import moment from 'moment';

export interface DateRangeData {
    start: Date;
    end: Date;
}

export interface PresetOption {
    labelKey: string;
    icon: string;
    getRange: () => { start: Date; end: Date };
}

@Component({
    selector: 'app-date-range-dialog',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        ReactiveFormsModule,
        MatDialogModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatButtonModule,
        MatIconModule,
        MatChipsModule,
        MatTooltipModule,
        MatDatepickerModule,
        MatMomentDateModule,
        TranslatePipe,
    ],
    templateUrl: './date-range-dialog.component.html',
    styleUrl: './date-range-dialog.component.css',
})
export class DateRangeDialogComponent implements OnInit {
    hours: string[] = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'));
    minutes: string[] = Array.from({ length: 60 }, (_, i) => String(i).padStart(2, '0'));

    rangeForm = new FormGroup({
        startDate: new FormControl<Date>(moment().subtract(1, 'day').toDate(), [Validators.required]),
        startHour: new FormControl<string>('00', [Validators.required]),
        startMinute: new FormControl<string>('00', [Validators.required]),
        endDate: new FormControl<Date>(moment().toDate(), [Validators.required]),
        endHour: new FormControl<string>('23', [Validators.required]),
        endMinute: new FormControl<string>('59', [Validators.required]),
    });

    presets: PresetOption[] = [
        {
            labelKey: 'TRANSACTION.DATE_RANGE.PRESET_15M',
            icon: 'schedule',
            getRange: () => ({
                start: moment().subtract(15, 'minutes').toDate(),
                end: moment().toDate()
            })
        },
        {
            labelKey: 'TRANSACTION.DATE_RANGE.PRESET_1H',
            icon: 'hourglass_top',
            getRange: () => ({
                start: moment().subtract(1, 'hour').toDate(),
                end: moment().toDate()
            })
        },
        {
            labelKey: 'TRANSACTION.DATE_RANGE.PRESET_6H',
            icon: 'history_toggle_off',
            getRange: () => ({
                start: moment().subtract(6, 'hours').toDate(),
                end: moment().toDate()
            })
        },
        {
            labelKey: 'TRANSACTION.DATE_RANGE.PRESET_24H',
            icon: 'today',
            getRange: () => ({
                start: moment().subtract(24, 'hours').toDate(),
                end: moment().toDate()
            })
        },
        {
            labelKey: 'TRANSACTION.DATE_RANGE.PRESET_7D',
            icon: 'date_range',
            getRange: () => ({
                start: moment().subtract(7, 'days').toDate(),
                end: moment().toDate()
            })
        },
        {
            labelKey: 'TRANSACTION.DATE_RANGE.PRESET_TODAY',
            icon: 'wb_sunny',
            getRange: () => ({
                start: moment().startOf('day').toDate(),
                end: moment().toDate()
            })
        },
        {
            labelKey: 'TRANSACTION.DATE_RANGE.PRESET_YESTERDAY',
            icon: 'event_repeat',
            getRange: () => ({
                start: moment().subtract(1, 'day').startOf('day').toDate(),
                end: moment().subtract(1, 'day').endOf('day').toDate()
            })
        }
    ];

    constructor(
        public dialogRef: MatDialogRef<DateRangeDialogComponent>,
        @Inject(MAT_DIALOG_DATA) public data: DateRangeData | null
    ) {}

    ngOnInit(): void {
        if (this.data) {
            const startMoment = moment(this.data.start || moment().subtract(1, 'day'));
            const endMoment = moment(this.data.end || moment());

            this.rangeForm.patchValue({
                startDate: startMoment.toDate(),
                startHour: startMoment.format('HH'),
                startMinute: startMoment.format('mm'),
                endDate: endMoment.toDate(),
                endHour: endMoment.format('HH'),
                endMinute: endMoment.format('mm'),
            });
        }
    }

    applyPreset(preset: PresetOption): void {
        const { start, end } = preset.getRange();
        const startMoment = moment(start);
        const endMoment = moment(end);

        this.rangeForm.patchValue({
            startDate: startMoment.toDate(),
            startHour: startMoment.format('HH'),
            startMinute: startMoment.format('mm'),
            endDate: endMoment.toDate(),
            endHour: endMoment.format('HH'),
            endMinute: endMoment.format('mm'),
        });
    }

    onApply(): void {
        if (this.rangeForm.invalid) return;

        const val = this.rangeForm.value;
        const start = moment(val.startDate)
            .hour(Number(val.startHour || '00'))
            .minute(Number(val.startMinute || '00'))
            .second(0)
            .millisecond(0)
            .toDate();

        const end = moment(val.endDate)
            .hour(Number(val.endHour || '23'))
            .minute(Number(val.endMinute || '59'))
            .second(59)
            .millisecond(999)
            .toDate();

        this.dialogRef.close({ start, end });
    }

    onCancel(): void {
        this.dialogRef.close();
    }
}
