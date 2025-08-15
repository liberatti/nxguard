import {Component} from '@angular/core';
import {HashLocationStrategy, LocationStrategy} from '@angular/common';
import {RouterOutlet} from '@angular/router';

@Component({
    selector: 'app-root',
    standalone: true,
    imports: [RouterOutlet],
    template: '<router-outlet></router-outlet>',
    providers: [
        {provide: LocationStrategy, useClass: HashLocationStrategy},
        {provide: 'LOCALSTORAGE', useValue: window.localStorage}
    ],
})
export class AppComponent {


}