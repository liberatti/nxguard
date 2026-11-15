import { Injectable, Injector } from '@angular/core';
import { Observable } from 'rxjs';
import { APIService } from './api.service';
import { IpxaStats } from '../models/config';

@Injectable({
    providedIn: 'root'
})
export class IpxaService extends APIService<IpxaStats, string> {
    constructor(protected override injector: Injector) {
        super(injector, 'ipxa');
    }

    getStats(): Observable<any> {
        return this.httpClient.get<any>(this.END_POINT + '/stats');
    }
}
