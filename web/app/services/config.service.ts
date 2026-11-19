import { Injectable, Injector } from "@angular/core";
import { APIService } from "./api.service";
import { Config, Health } from "../models/config";
import { LocalStorageService } from "./localstorage.service";
import { Observable } from "rxjs";
import { Page } from "../models/shared";

@Injectable({
    providedIn: 'root'
})
export class ConfigService extends APIService<Config, string> {

    constructor(
        protected override injector: Injector,
        private localStorage: LocalStorageService
    ) {
        super(injector, 'config')
    }

    getActive(): Observable<Config> {
        return this.httpClient.get<Config>(this.END_POINT);
    }

    override update(id: string, data: Config): Observable<Config> {
        return this.httpClient.put<Config>(this.END_POINT, data);
    }
    healthCheck(): Observable<any> {
        return this.httpClient.get<any>(this.END_POINT + "/health");
    }

    applyConfig(): Observable<any> {
        return this.httpClient.post<any>(this.END_POINT + "/apply", {});
    }

    getChanges(): Observable<any> {
        return this.httpClient.get<any>(this.END_POINT + "/changes");
    }

    downloadConfig(): Observable<Blob> {
        const httpOptions = {
            responseType: 'blob' as 'json'
        };
        return this.httpClient.get<Blob>(this.END_POINT + "/backup", httpOptions);
    }

    uploadConfig(data: FormData): Observable<any> {
        return this.httpClient.post<any>(this.END_POINT + "/backup", data);
    }
    get_geo_countries(): Observable<any[]> {
        return this.httpClient.get<any[]>(this.END_POINT + "/geo");
    }

    getHistory(page: number = 1, perPage: number = 20): Observable<any> {
        return this.httpClient.get<any>(`${this.END_POINT}/history`, {
            params: { page: page.toString(), per_page: perPage.toString() }
        });
    }

    getVersionDiff(scn: string, baseScn?: string): Observable<any> {
        const params: any = {};
        if (baseScn) {
            params.base_scn = baseScn;
        }
        return this.httpClient.get<any>(`${this.END_POINT}/history/${scn}/diff`, { params });
    }

    applyHistoryVersion(scn: string): Observable<any> {
        return this.httpClient.post<any>(`${this.END_POINT}/history/${scn}/apply`, {});
    }
}

@Injectable({
    providedIn: 'root'
})
export class HealthService extends APIService<Health, string> {

    constructor(
        protected override injector: Injector
    ) {
        super(injector, 'config')
    }
    check(): Observable<any> {
        return this.httpClient.get<any>(this.END_POINT + "/health");
    }
}