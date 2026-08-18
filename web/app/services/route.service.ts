import { Injectable, Injector } from '@angular/core';
import { Observable } from 'rxjs';
import { Route } from '../models/service';
import { APIService } from './api.service';

@Injectable({
    providedIn: 'root'
})
export class RouteService extends APIService<Route, string> {

    constructor(
        protected override injector: Injector
    ) {
        super(injector, 'route');
    }

    getByServiceId(serviceId: string | number): Observable<Route[]> {
        return this.httpClient.get<Route[]>(`${this.END_POINT}?service_id=${serviceId}`);
    }
}
