import { Injectable } from '@angular/core';

export interface CountryInfo {
    code: string;
    name: string;
    region: string;
}

export interface RegionGroup {
    name: string;
    countries: CountryInfo[];
}

const COUNTRY_DATABASE: Record<string, { name: string; region: string }> = {
    // Americas
    US: { name: 'United States', region: 'Americas' },
    CA: { name: 'Canada', region: 'Americas' },
    MX: { name: 'Mexico', region: 'Americas' },
    BR: { name: 'Brazil', region: 'Americas' },
    AR: { name: 'Argentina', region: 'Americas' },
    CL: { name: 'Chile', region: 'Americas' },
    CO: { name: 'Colombia', region: 'Americas' },
    PE: { name: 'Peru', region: 'Americas' },
    UY: { name: 'Uruguay', region: 'Americas' },
    VE: { name: 'Venezuela', region: 'Americas' },
    PA: { name: 'Panama', region: 'Americas' },
    CR: { name: 'Costa Rica', region: 'Americas' },
    CU: { name: 'Cuba', region: 'Americas' },
    DO: { name: 'Dominican Republic', region: 'Americas' },
    EC: { name: 'Ecuador', region: 'Americas' },
    GT: { name: 'Guatemala', region: 'Americas' },
    JM: { name: 'Jamaica', region: 'Americas' },
    PR: { name: 'Puerto Rico', region: 'Americas' },
    TT: { name: 'Trinidad & Tobago', region: 'Americas' },
    BO: { name: 'Bolivia', region: 'Americas' },
    PY: { name: 'Paraguay', region: 'Americas' },

    // Europe
    GB: { name: 'United Kingdom', region: 'Europe' },
    DE: { name: 'Germany', region: 'Europe' },
    FR: { name: 'France', region: 'Europe' },
    IT: { name: 'Italy', region: 'Europe' },
    ES: { name: 'Spain', region: 'Europe' },
    PT: { name: 'Portugal', region: 'Europe' },
    NL: { name: 'Netherlands', region: 'Europe' },
    BE: { name: 'Belgium', region: 'Europe' },
    CH: { name: 'Switzerland', region: 'Europe' },
    AT: { name: 'Austria', region: 'Europe' },
    SE: { name: 'Sweden', region: 'Europe' },
    NO: { name: 'Norway', region: 'Europe' },
    DK: { name: 'Denmark', region: 'Europe' },
    FI: { name: 'Finland', region: 'Europe' },
    PL: { name: 'Poland', region: 'Europe' },
    CZ: { name: 'Czech Republic', region: 'Europe' },
    IE: { name: 'Ireland', region: 'Europe' },
    GR: { name: 'Greece', region: 'Europe' },
    RO: { name: 'Romania', region: 'Europe' },
    HU: { name: 'Hungary', region: 'Europe' },
    UA: { name: 'Ukraine', region: 'Europe' },
    RU: { name: 'Russia', region: 'Europe' },
    BY: { name: 'Belarus', region: 'Europe' },
    BG: { name: 'Bulgaria', region: 'Europe' },
    HR: { name: 'Croatia', region: 'Europe' },
    SK: { name: 'Slovakia', region: 'Europe' },
    EE: { name: 'Estonia', region: 'Europe' },
    LV: { name: 'Latvia', region: 'Europe' },
    LT: { name: 'Lithuania', region: 'Europe' },
    IS: { name: 'Iceland', region: 'Europe' },
    RS: { name: 'Serbia', region: 'Europe' },
    SI: { name: 'Slovenia', region: 'Europe' },
    LU: { name: 'Luxembourg', region: 'Europe' },
    CY: { name: 'Cyprus', region: 'Europe' },
    MT: { name: 'Malta', region: 'Europe' },

    // Asia-Pacific
    CN: { name: 'China', region: 'Asia-Pacific' },
    JP: { name: 'Japan', region: 'Asia-Pacific' },
    KR: { name: 'South Korea', region: 'Asia-Pacific' },
    IN: { name: 'India', region: 'Asia-Pacific' },
    AU: { name: 'Australia', region: 'Asia-Pacific' },
    NZ: { name: 'New Zealand', region: 'Asia-Pacific' },
    SG: { name: 'Singapore', region: 'Asia-Pacific' },
    MY: { name: 'Malaysia', region: 'Asia-Pacific' },
    TH: { name: 'Thailand', region: 'Asia-Pacific' },
    PH: { name: 'Philippines', region: 'Asia-Pacific' },
    VN: { name: 'Vietnam', region: 'Asia-Pacific' },
    ID: { name: 'Indonesia', region: 'Asia-Pacific' },
    TW: { name: 'Taiwan', region: 'Asia-Pacific' },
    HK: { name: 'Hong Kong', region: 'Asia-Pacific' },
    PK: { name: 'Pakistan', region: 'Asia-Pacific' },
    BD: { name: 'Bangladesh', region: 'Asia-Pacific' },
    LK: { name: 'Sri Lanka', region: 'Asia-Pacific' },
    KH: { name: 'Cambodia', region: 'Asia-Pacific' },
    MM: { name: 'Myanmar', region: 'Asia-Pacific' },
    NP: { name: 'Nepal', region: 'Asia-Pacific' },
    MN: { name: 'Mongolia', region: 'Asia-Pacific' },
    KZ: { name: 'Kazakhstan', region: 'Asia-Pacific' },
    UZ: { name: 'Uzbekistan', region: 'Asia-Pacific' },

    // Middle East & Africa
    AE: { name: 'United Arab Emirates', region: 'Middle East & Africa' },
    SA: { name: 'Saudi Arabia', region: 'Middle East & Africa' },
    IL: { name: 'Israel', region: 'Middle East & Africa' },
    TR: { name: 'Turkey', region: 'Middle East & Africa' },
    ZA: { name: 'South Africa', region: 'Middle East & Africa' },
    NG: { name: 'Nigeria', region: 'Middle East & Africa' },
    EG: { name: 'Egypt', region: 'Middle East & Africa' },
    KE: { name: 'Kenya', region: 'Middle East & Africa' },
    MA: { name: 'Morocco', region: 'Middle East & Africa' },
    GH: { name: 'Ghana', region: 'Middle East & Africa' },
    QA: { name: 'Qatar', region: 'Middle East & Africa' },
    KW: { name: 'Kuwait', region: 'Middle East & Africa' },
    OM: { name: 'Oman', region: 'Middle East & Africa' },
    BH: { name: 'Bahrain', region: 'Middle East & Africa' },
    JO: { name: 'Jordan', region: 'Middle East & Africa' },
    LB: { name: 'Lebanon', region: 'Middle East & Africa' },
    IQ: { name: 'Iraq', region: 'Middle East & Africa' },
    IR: { name: 'Iran', region: 'Middle East & Africa' },
    DZ: { name: 'Algeria', region: 'Middle East & Africa' },
    TN: { name: 'Tunisia', region: 'Middle East & Africa' },
    ET: { name: 'Ethiopia', region: 'Middle East & Africa' },
    TZ: { name: 'Tanzania', region: 'Middle East & Africa' },
    UG: { name: 'Uganda', region: 'Middle East & Africa' },
    AO: { name: 'Angola', region: 'Middle East & Africa' },

    // Fallbacks
    None: { name: 'None', region: 'Other / Global' },
    Unknown: { name: 'Unknown', region: 'Other / Global' }
};

const REGION_ORDER = [
    'Americas',
    'Europe',
    'Asia-Pacific',
    'Middle East & Africa',
    'Other / Global'
];

@Injectable({
    providedIn: 'root'
})
export class GeoCountryService {

    getCountryInfo(code: string): CountryInfo {
        const cleanCode = (code || '').trim();
        const upper = cleanCode.toUpperCase();
        const entry = COUNTRY_DATABASE[upper] || COUNTRY_DATABASE[cleanCode];

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

        const groupsMap = new Map<string, CountryInfo[]>();
        for (const r of REGION_ORDER) {
            groupsMap.set(r, []);
        }

        for (const item of filtered) {
            const list = groupsMap.get(item.region) || [];
            list.push(item);
            groupsMap.set(item.region, list);
        }

        const result: RegionGroup[] = [];
        for (const r of REGION_ORDER) {
            const items = groupsMap.get(r) || [];
            if (items.length > 0) {
                // sort alphabetically by name
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
        for (const [code, info] of Object.entries(COUNTRY_DATABASE)) {
            if (code === 'None' || code === 'Unknown') continue;
            list.push({
                code,
                name: info.name,
                region: info.region
            });
        }
        return list.sort((a, b) => a.name.localeCompare(b.name));
    }
}
