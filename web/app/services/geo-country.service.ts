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

export interface ContinentRegion {
    id: string;
    nameKey: string;
    defaultName: string;
    countries: CountryInfo[];
}

// 6 standard continents with exact country counts matching ISO / UN M49
const CONTINENT_COUNTRIES: { id: string; nameKey: string; defaultName: string; countries: { code: string; name: string }[] }[] = [
    {
        id: 'africa',
        nameKey: 'SENSOR.CONTINENTS.AFRICA',
        defaultName: 'África',
        countries: [
            { code: 'DZ', name: 'Algeria' },
            { code: 'AO', name: 'Angola' },
            { code: 'BJ', name: 'Benin' },
            { code: 'BW', name: 'Botswana' },
            { code: 'BF', name: 'Burkina Faso' },
            { code: 'BI', name: 'Burundi' },
            { code: 'CV', name: 'Cabo Verde' },
            { code: 'CM', name: 'Cameroon' },
            { code: 'CF', name: 'Central African Republic' },
            { code: 'TD', name: 'Chad' },
            { code: 'KM', name: 'Comoros' },
            { code: 'CG', name: 'Congo' },
            { code: 'CD', name: 'DR Congo' },
            { code: 'CI', name: 'Ivory Coast' },
            { code: 'DJ', name: 'Djibouti' },
            { code: 'EG', name: 'Egypt' },
            { code: 'GQ', name: 'Equatorial Guinea' },
            { code: 'ER', name: 'Eritrea' },
            { code: 'SZ', name: 'Eswatini' },
            { code: 'ET', name: 'Ethiopia' },
            { code: 'GA', name: 'Gabon' },
            { code: 'GM', name: 'Gambia' },
            { code: 'GH', name: 'Ghana' },
            { code: 'GN', name: 'Guinea' },
            { code: 'GW', name: 'Guinea-Bissau' },
            { code: 'KE', name: 'Kenya' },
            { code: 'LS', name: 'Lesotho' },
            { code: 'LR', name: 'Liberia' },
            { code: 'LY', name: 'Libya' },
            { code: 'MG', name: 'Madagascar' },
            { code: 'MW', name: 'Malawi' },
            { code: 'ML', name: 'Mali' },
            { code: 'MR', name: 'Mauritania' },
            { code: 'MU', name: 'Mauritius' },
            { code: 'MA', name: 'Morocco' },
            { code: 'MZ', name: 'Mozambique' },
            { code: 'NA', name: 'Namibia' },
            { code: 'NE', name: 'Niger' },
            { code: 'NG', name: 'Nigeria' },
            { code: 'RW', name: 'Rwanda' },
            { code: 'ST', name: 'Sao Tome and Principe' },
            { code: 'SN', name: 'Senegal' },
            { code: 'SC', name: 'Seychelles' },
            { code: 'SL', name: 'Sierra Leone' },
            { code: 'SO', name: 'Somalia' },
            { code: 'ZA', name: 'South Africa' },
            { code: 'SS', name: 'South Sudan' },
            { code: 'SD', name: 'Sudan' },
            { code: 'TZ', name: 'Tanzania' },
            { code: 'TG', name: 'Togo' },
            { code: 'TN', name: 'Tunisia' },
            { code: 'UG', name: 'Uganda' },
            { code: 'ZM', name: 'Zambia' },
            { code: 'ZW', name: 'Zimbabwe' }
        ]
    },
    {
        id: 'north_america',
        nameKey: 'SENSOR.CONTINENTS.NORTH_AMERICA',
        defaultName: 'América do Norte',
        countries: [
            { code: 'CA', name: 'Canada' },
            { code: 'MX', name: 'Mexico' },
            { code: 'US', name: 'United States' }
        ]
    },
    {
        id: 'south_america',
        nameKey: 'SENSOR.CONTINENTS.SOUTH_AMERICA',
        defaultName: 'América do Sul',
        countries: [
            { code: 'AR', name: 'Argentina' },
            { code: 'BO', name: 'Bolivia' },
            { code: 'BR', name: 'Brazil' },
            { code: 'CL', name: 'Chile' },
            { code: 'CO', name: 'Colombia' },
            { code: 'EC', name: 'Ecuador' },
            { code: 'GY', name: 'Guyana' },
            { code: 'PY', name: 'Paraguay' },
            { code: 'PE', name: 'Peru' },
            { code: 'SR', name: 'Suriname' },
            { code: 'UY', name: 'Uruguay' },
            { code: 'VE', name: 'Venezuela' }
        ]
    },
    {
        id: 'asia',
        nameKey: 'SENSOR.CONTINENTS.ASIA',
        defaultName: 'Ásia',
        countries: [
            { code: 'AF', name: 'Afghanistan' },
            { code: 'AM', name: 'Armenia' },
            { code: 'AZ', name: 'Azerbaijan' },
            { code: 'BH', name: 'Bahrain' },
            { code: 'BD', name: 'Bangladesh' },
            { code: 'BT', name: 'Bhutan' },
            { code: 'BN', name: 'Brunei' },
            { code: 'KH', name: 'Cambodia' },
            { code: 'CN', name: 'China' },
            { code: 'CY', name: 'Cyprus' },
            { code: 'GE', name: 'Georgia' },
            { code: 'HK', name: 'Hong Kong' },
            { code: 'IN', name: 'India' },
            { code: 'ID', name: 'Indonesia' },
            { code: 'IR', name: 'Iran' },
            { code: 'IQ', name: 'Iraq' },
            { code: 'IL', name: 'Israel' },
            { code: 'JP', name: 'Japan' },
            { code: 'JO', name: 'Jordan' },
            { code: 'KZ', name: 'Kazakhstan' },
            { code: 'KW', name: 'Kuwait' },
            { code: 'KG', name: 'Kyrgyzstan' },
            { code: 'LA', name: 'Laos' },
            { code: 'LB', name: 'Lebanon' },
            { code: 'MY', name: 'Malaysia' },
            { code: 'MV', name: 'Maldives' },
            { code: 'MN', name: 'Mongolia' },
            { code: 'MM', name: 'Myanmar' },
            { code: 'NP', name: 'Nepal' },
            { code: 'KP', name: 'North Korea' },
            { code: 'OM', name: 'Oman' },
            { code: 'PK', name: 'Pakistan' },
            { code: 'PH', name: 'Philippines' },
            { code: 'QA', name: 'Qatar' },
            { code: 'SA', name: 'Saudi Arabia' },
            { code: 'SG', name: 'Singapore' },
            { code: 'KR', name: 'South Korea' },
            { code: 'LK', name: 'Sri Lanka' },
            { code: 'SY', name: 'Syria' },
            { code: 'TW', name: 'Taiwan' },
            { code: 'TJ', name: 'Tajikistan' },
            { code: 'TH', name: 'Thailand' },
            { code: 'TL', name: 'Timor-Leste' },
            { code: 'TR', name: 'Turkey' },
            { code: 'TM', name: 'Turkmenistan' },
            { code: 'AE', name: 'United Arab Emirates' },
            { code: 'UZ', name: 'Uzbekistan' },
            { code: 'VN', name: 'Vietnam' },
            { code: 'YE', name: 'Yemen' }
        ]
    },
    {
        id: 'europe',
        nameKey: 'SENSOR.CONTINENTS.EUROPE',
        defaultName: 'Europa',
        countries: [
            { code: 'AL', name: 'Albania' },
            { code: 'AD', name: 'Andorra' },
            { code: 'AT', name: 'Austria' },
            { code: 'BY', name: 'Belarus' },
            { code: 'BE', name: 'Belgium' },
            { code: 'BA', name: 'Bosnia and Herzegovina' },
            { code: 'BG', name: 'Bulgaria' },
            { code: 'HR', name: 'Croatia' },
            { code: 'CZ', name: 'Czech Republic' },
            { code: 'DK', name: 'Denmark' },
            { code: 'EE', name: 'Estonia' },
            { code: 'FI', name: 'Finland' },
            { code: 'FR', name: 'France' },
            { code: 'DE', name: 'Germany' },
            { code: 'GR', name: 'Greece' },
            { code: 'HU', name: 'Hungary' },
            { code: 'IS', name: 'Iceland' },
            { code: 'IE', name: 'Ireland' },
            { code: 'IT', name: 'Italy' },
            { code: 'LV', name: 'Latvia' },
            { code: 'LI', name: 'Liechtenstein' },
            { code: 'LT', name: 'Lithuania' },
            { code: 'LU', name: 'Luxembourg' },
            { code: 'MT', name: 'Malta' },
            { code: 'MD', name: 'Moldova' },
            { code: 'MC', name: 'Monaco' },
            { code: 'ME', name: 'Montenegro' },
            { code: 'NL', name: 'Netherlands' },
            { code: 'MK', name: 'North Macedonia' },
            { code: 'NO', name: 'Norway' },
            { code: 'PL', name: 'Poland' },
            { code: 'PT', name: 'Portugal' },
            { code: 'RO', name: 'Romania' },
            { code: 'RU', name: 'Russia' },
            { code: 'SM', name: 'San Marino' },
            { code: 'RS', name: 'Serbia' },
            { code: 'SK', name: 'Slovakia' },
            { code: 'SI', name: 'Slovenia' },
            { code: 'ES', name: 'Spain' },
            { code: 'SE', name: 'Sweden' },
            { code: 'CH', name: 'Switzerland' },
            { code: 'UA', name: 'Ukraine' },
            { code: 'GB', name: 'United Kingdom' },
            { code: 'VA', name: 'Vatican City' }
        ]
    },
    {
        id: 'oceania',
        nameKey: 'SENSOR.CONTINENTS.OCEANIA',
        defaultName: 'Oceania',
        countries: [
            { code: 'AU', name: 'Australia' },
            { code: 'FJ', name: 'Fiji' },
            { code: 'KI', name: 'Kiribati' },
            { code: 'MH', name: 'Marshall Islands' },
            { code: 'FM', name: 'Micronesia' },
            { code: 'NR', name: 'Nauru' },
            { code: 'NZ', name: 'New Zealand' },
            { code: 'PW', name: 'Palau' },
            { code: 'PG', name: 'Papua New Guinea' },
            { code: 'WS', name: 'Samoa' },
            { code: 'SB', name: 'Solomon Islands' },
            { code: 'TO', name: 'Tonga' },
            { code: 'TV', name: 'Tuvalu' },
            { code: 'VU', name: 'Vanuatu' }
        ]
    }
];

const CODE_TO_COUNTRY: Record<string, { name: string; region: string }> = {};
for (const continent of CONTINENT_COUNTRIES) {
    for (const c of continent.countries) {
        CODE_TO_COUNTRY[c.code] = { name: c.name, region: continent.defaultName };
    }
}

// Global fallbacks
CODE_TO_COUNTRY['None'] = { name: 'None', region: 'Other / Global' };
CODE_TO_COUNTRY['Unknown'] = { name: 'Unknown', region: 'Other / Global' };

@Injectable({
    providedIn: 'root'
})
export class GeoCountryService {

    getContinentRegions(searchQuery: string = ''): ContinentRegion[] {
        const query = (searchQuery || '').trim().toLowerCase();

        return CONTINENT_COUNTRIES.map(continent => {
            const countries: CountryInfo[] = continent.countries
                .filter(c => {
                    if (!query) return true;
                    const matchCode = c.code.toLowerCase().includes(query);
                    const matchName = c.name.toLowerCase().includes(query);
                    const matchRegion = continent.defaultName.toLowerCase().includes(query);
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
        const entry = CODE_TO_COUNTRY[upper] || CODE_TO_COUNTRY[cleanCode];

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

        const regionNames = ['África', 'América do Norte', 'América do Sul', 'Ásia', 'Europa', 'Oceania', 'Other / Global'];
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
        for (const [code, info] of Object.entries(CODE_TO_COUNTRY)) {
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
