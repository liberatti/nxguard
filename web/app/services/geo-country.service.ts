import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { catchError, map, shareReplay, tap } from 'rxjs/operators';
import { FeedService } from './feed.service';

export interface CountryInfo {
    code: string;
    name: string;
    region: string;
}

export interface RegionGroup {
    name: string;
    countries: CountryInfo[];
}

export interface ContinentRegion {
    id: string;
    nameKey: string;
    defaultName: string;
    countries: CountryInfo[];
}

@Injectable({
    providedIn: 'root'
})
export class GeoCountryService {
    private continentRegions: ContinentRegion[] = [];
    private codeToCountry: Record<string, { name: string; region: string }> = {
        'None': { name: 'None', region: 'Other / Global' },
        'Unknown': { name: 'Unknown', region: 'Other / Global' }
    };
    private loadCache$: Observable<ContinentRegion[]> | null = null;

    constructor(private feedService: FeedService) {
        this.loadGeoCountries().subscribe();
    }

    loadGeoCountries(forceRefresh: boolean = false): Observable<ContinentRegion[]> {
        if (!this.loadCache$ || forceRefresh) {
            this.loadCache$ = this.feedService.get_geo_countries().pipe(
                map((data: any) => {
                    const list = Array.isArray(data) ? data : (data?.data || []);
                    return this.normalizeContinents(list);
                }),
                tap((continents: ContinentRegion[]) => {
                    if (continents.length > 0) {
                        this.setContinentData(continents);
                    }
                }),
                catchError(err => {
                    console.error('Failed to load geo countries from feed service:', err);
                    return of(this.continentRegions);
                }),
                shareReplay(1)
            );
        }
        return this.loadCache$;
    }

    loadContinentRegions(forceRefresh: boolean = false): Observable<ContinentRegion[]> {
        return this.loadGeoCountries(forceRefresh);
    }

    getContinentRegions(searchQuery: string = ''): ContinentRegion[] {
        const query = (searchQuery || '').trim().toLowerCase();

        return this.continentRegions.map(continent => {
            const countries: CountryInfo[] = (continent.countries || [])
                .filter(c => {
                    if (!query) return true;
                    const matchCode = c.code.toLowerCase().includes(query);
                    const matchName = c.name.toLowerCase().includes(query);
                    const matchRegion = (continent.defaultName || '').toLowerCase().includes(query);
                    return matchCode || matchName || matchRegion;
                })
                .map(c => ({
                    code: c.code,
                    name: c.name,
                    region: continent.defaultName
                }));

            return {
                id: continent.id,
                nameKey: continent.nameKey,
                defaultName: continent.defaultName,
                countries: countries.sort((a, b) => a.name.localeCompare(b.name))
            };
        });
    }

    getCountryInfo(code: string): CountryInfo {
        const cleanCode = (code || '').trim();
        const upper = cleanCode.toUpperCase();
        const entry = this.codeToCountry[upper] || this.codeToCountry[cleanCode];

        if (entry) {
            return {
                code: cleanCode,
                name: entry.name,
                region: entry.region
            };
        }

        return {
            code: cleanCode,
            name: cleanCode,
            region: 'Other / Global'
        };
    }

    groupCountriesByRegion(codes: string[], searchQuery: string = ''): RegionGroup[] {
        if (!codes || codes.length === 0) {
            return [];
        }

        const query = (searchQuery || '').trim().toLowerCase();
        const seen = new Set<string>();
        const filtered: CountryInfo[] = [];

        for (const code of codes) {
            if (!code || seen.has(code)) continue;
            seen.add(code);
            const info = this.getCountryInfo(code);

            if (query) {
                const matchCode = info.code.toLowerCase().includes(query);
                const matchName = info.name.toLowerCase().includes(query);
                const matchRegion = info.region.toLowerCase().includes(query);
                if (!matchCode && !matchName && !matchRegion) {
                    continue;
                }
            }

            filtered.push(info);
        }

        const regionNames = this.continentRegions.length > 0
            ? [...this.continentRegions.map(c => c.defaultName), 'Other / Global']
            : ['África', 'América do Norte', 'América do Sul', 'Ásia', 'Europa', 'Oceania', 'Other / Global'];

        const groupsMap = new Map<string, CountryInfo[]>();
        for (const r of regionNames) {
            groupsMap.set(r, []);
        }

        for (const item of filtered) {
            const list = groupsMap.get(item.region) || [];
            list.push(item);
            groupsMap.set(item.region, list);
        }

        const result: RegionGroup[] = [];
        for (const r of regionNames) {
            const items = groupsMap.get(r) || [];
            if (items.length > 0) {
                items.sort((a, b) => a.name.localeCompare(b.name));
                result.push({
                    name: r,
                    countries: items
                });
            }
        }

        return result;
    }

    getAllCountries(): CountryInfo[] {
        const list: CountryInfo[] = [];
        for (const [code, info] of Object.entries(this.codeToCountry)) {
            if (code === 'None' || code === 'Unknown') continue;
            list.push({
                code,
                name: info.name,
                region: info.region
            });
        }
        return list.sort((a, b) => a.name.localeCompare(b.name));
    }

    private normalizeContinents(data: any[]): ContinentRegion[] {
        return data.map(item => {
            let nameKey = item.nameKey || `SENSOR.CONTINENTS.${item.id?.toUpperCase()}`;
            if (nameKey.startsWith('GEOIP_DIALOG.')) {
                nameKey = nameKey.replace('GEOIP_DIALOG.', 'SENSOR.');
            }
            return {
                id: item.id,
                nameKey,
                defaultName: item.defaultName || item.name,
                countries: (item.countries || []).map((c: any) => ({
                    code: c.code,
                    name: c.name,
                    region: item.defaultName || item.name
                }))
            };
        });
    }

    private setContinentData(continents: ContinentRegion[]): void {
        this.continentRegions = continents;
        this.codeToCountry = {
            'None': { name: 'None', region: 'Other / Global' },
            'Unknown': { name: 'Unknown', region: 'Other / Global' }
        };
        for (const continent of continents) {
            for (const c of continent.countries) {
                this.codeToCountry[c.code] = { name: c.name, region: continent.defaultName };
            }
        }
    }
}
