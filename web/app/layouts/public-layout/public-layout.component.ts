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
        const savedLang = this.localStorage.get('lang');
        if (this.localStorage.exists('ui_config')) {
            this.config = this.localStorage.get('ui_config');
            if (savedLang && this.config) {
                this.config.locale = savedLang;
                this.localStorage.set('ui_config', this.config);
            }
        } else {
            this.config = <FrontendConfig>{ locale: savedLang || 'en_US', navResource: "transaction", sidenavOpened: false };
            this.localStorage.set('ui_config', this.config);
        }
        const langKey = savedLang || (typeof this.config.locale === 'object' ? (this.config.locale?.key || this.config.locale?.id || 'en_US') : (this.config.locale || 'en_US'));
        this.translate.use(langKey);
        moment.locale(langKey);
    }
}
