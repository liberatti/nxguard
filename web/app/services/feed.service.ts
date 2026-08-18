import {Injectable, Injector} from "@angular/core";
import {APIService} from "./api.service";
import {Feed} from "../models/feed";
import {LocalStorageService} from "./localstorage.service";

@Injectable({
    providedIn: 'root'
})
export class FeedService extends APIService<Feed, string> {

    constructor(
        protected override injector: Injector
    ) {
        super(injector, 'feed')
    }

    // Lazy injection method for LocalStorageService
    private get localStorage(): LocalStorageService {
        return this.injector.get(LocalStorageService);
    }
}