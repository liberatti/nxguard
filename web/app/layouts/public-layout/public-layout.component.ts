import { AfterViewInit, Component, Injector } from '@angular/core';
import { RouterModule } from '@angular/router';
import { FrontendConfig } from "../../models/shared";
import * as moment from "moment/moment";
import { LocalStorageService } from "../../services/localstorage.service";
import { TranslateService } from "@ngx-translate/core";

@Component({
    selector: 'app-public-layout',
    standalone: true,
    imports: [RouterModule],
    templateUrl: './public-layout.component.html'
})
export class PublicLayoutComponent implements AfterViewInit {
    config: FrontendConfig = <FrontendConfig>{ locale: { key: 'en_US' }, navResource: "transaction", sidenavOpened: false };

    constructor(
        private localStorage: LocalStorageService,
        private translate: TranslateService,
        protected injector: Injector,
    ) {
    }

    ngAfterViewInit(): void {
        if (this.localStorage.exists('ui_config')) {
            this.config = this.localStorage.get('ui_config');
        } else {
            this.localStorage.set('ui_config', this.config);
        }
        const langKey = typeof this.config.locale === 'object' ? (this.config.locale?.key || this.config.locale?.id || 'en_US') : (this.config.locale || 'en_US');
        this.translate.use(langKey);
        moment.locale(langKey);
    }
}
