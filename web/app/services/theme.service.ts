import { Injectable, signal } from '@angular/core';
import { LocalStorageService } from './localstorage.service';

@Injectable({
    providedIn: 'root'
})
export class ThemeService {
    private readonly THEME_KEY = 'nxguard_theme';
    isDarkMode = signal<boolean>(false);

    constructor(private localStorage: LocalStorageService) {
        this.initTheme();
    }

    private initTheme(): void {
        const savedTheme = this.localStorage.get(this.THEME_KEY);
        if (savedTheme !== null) {
            const isDark = savedTheme === 'dark';
            this.setTheme(isDark);
        } else {
            // Check system preference
            const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
            this.setTheme(prefersDark);
        }
    }

    toggleTheme(): void {
        this.setTheme(!this.isDarkMode());
    }

    setTheme(isDark: boolean): void {
        this.isDarkMode.set(isDark);
        this.localStorage.set(this.THEME_KEY, isDark ? 'dark' : 'light');

        if (isDark) {
            document.body.classList.add('dark-theme');
        } else {
            document.body.classList.remove('dark-theme');
        }
    }
}
