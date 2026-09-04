import {Injectable, Injector} from "@angular/core";
import {APIService} from "./api.service";
import {Upstream} from "../models/upstream";

@Injectable({
    providedIn: 'root'
})
export class UpstreamService extends APIService<Upstream, string> {

    constructor(
        protected override injector: Injector
    ) {
        super(injector, 'upstream')
    }

    getStates(id: string) {
        return this.httpClient.get<any[]>(`${this.END_POINT}/${id}/states`);
    }
}
