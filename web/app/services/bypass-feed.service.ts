import { Injectable } from '@angular/core';

export interface BypassFeedInfo {
    name: string;
    category: string;
    categoryKey: string;
    icon: string;
    colorClass: string;
    description?: string;
}

export interface BypassCategoryGroup {
    id: string;
    name: string;
    key: string;
    icon: string;
    colorClass: string;
    providers: BypassFeedInfo[];
}

const CATEGORY_KEYS: Record<string, string> = {
    'Private & Local Networks': 'BYPASS_CATEGORY.LOCAL_NETWORKS',
    'Search Engine Crawlers': 'BYPASS_CATEGORY.SEARCH_CRAWLERS',
    'CDNs & Cloud Proxies': 'BYPASS_CATEGORY.CDN_CLOUD',
    'Monitoring & Healthchecks': 'BYPASS_CATEGORY.MONITORING',
    'Trusted & Custom Whitelists': 'BYPASS_CATEGORY.TRUSTED_LISTS'
};

const CATEGORY_ORDER = [
    { id: 'local', name: 'Private & Local Networks', key: 'BYPASS_CATEGORY.LOCAL_NETWORKS', icon: 'lan', colorClass: 'cat-local' },
    { id: 'cdn', name: 'CDNs & Cloud Proxies', key: 'BYPASS_CATEGORY.CDN_CLOUD', icon: 'cloud', colorClass: 'cat-cdn' },
    { id: 'crawlers', name: 'Search Engine Crawlers', key: 'BYPASS_CATEGORY.SEARCH_CRAWLERS', icon: 'smart_toy', colorClass: 'cat-bot' },
    { id: 'monitoring', name: 'Monitoring & Healthchecks', key: 'BYPASS_CATEGORY.MONITORING', icon: 'monitor_heart', colorClass: 'cat-monitor' },
    { id: 'trusted', name: 'Trusted & Custom Whitelists', key: 'BYPASS_CATEGORY.TRUSTED_LISTS', icon: 'verified_user', colorClass: 'cat-trusted' }
];

@Injectable({
    providedIn: 'root'
})
export class BypassFeedService {

    getFeedInfo(feedName: string): BypassFeedInfo {
        const cleanName = (feedName || '').trim();
        const lower = cleanName.toLowerCase();

        // Heuristic detection based on keywords
        let category = 'Trusted & Custom Whitelists';
        let icon = 'verified_user';
        let colorClass = 'cat-trusted';

        if (lower.includes('lan') || lower.includes('local') || lower.includes('rfc1918') || lower.includes('priv') || lower.includes('vpn') || lower.includes('internal') || lower.includes('loopback')) {
            category = 'Private & Local Networks';
            icon = 'lan';
            colorClass = 'cat-local';
        } else if (lower.includes('cdn') || lower.includes('cloud') || lower.includes('fastly') || lower.includes('akamai') || lower.includes('edge') || lower.includes('proxy')) {
            category = 'CDNs & Cloud Proxies';
            icon = 'cloud';
            colorClass = 'cat-cdn';
        } else if (lower.includes('bot') || lower.includes('crawl') || lower.includes('google') || lower.includes('bing') || lower.includes('apple') || lower.includes('spider') || lower.includes('duckduckgo')) {
            category = 'Search Engine Crawlers';
            icon = 'smart_toy';
            colorClass = 'cat-bot';
        } else if (lower.includes('uptime') || lower.includes('pingdom') || lower.includes('monitor') || lower.includes('health') || lower.includes('probe') || lower.includes('datadog')) {
            category = 'Monitoring & Healthchecks';
            icon = 'monitor_heart';
            colorClass = 'cat-monitor';
        }

        return {
            name: cleanName,
            category,
            categoryKey: CATEGORY_KEYS[category] || 'BYPASS_CATEGORY.TRUSTED_LISTS',
            icon,
            colorClass
        };
    }

    groupFeedsByCategory(feeds: string[], searchQuery: string = ''): BypassCategoryGroup[] {
        if (!feeds || feeds.length === 0) {
            return [];
        }

        const query = (searchQuery || '').trim().toLowerCase();
        const seen = new Set<string>();
        const list: BypassFeedInfo[] = [];

        for (const f of feeds) {
            const clean = (f || '').trim();
            if (!clean || seen.has(clean)) continue;
            seen.add(clean);
            const info = this.getFeedInfo(clean);

            if (query) {
                const matchName = info.name.toLowerCase().includes(query);
                const matchCategory = info.category.toLowerCase().includes(query);
                const matchDesc = (info.description || '').toLowerCase().includes(query);
                if (!matchName && !matchCategory && !matchDesc) {
                    continue;
                }
            }

            list.push(info);
        }

        const groupsMap = new Map<string, BypassFeedInfo[]>();
        for (const cat of CATEGORY_ORDER) {
            groupsMap.set(cat.name, []);
        }

        for (const item of list) {
            const current = groupsMap.get(item.category) || [];
            current.push(item);
            groupsMap.set(item.category, current);
        }

        const result: BypassCategoryGroup[] = [];
        for (const cat of CATEGORY_ORDER) {
            const items = groupsMap.get(cat.name) || [];
            if (items.length > 0) {
                items.sort((a, b) => a.name.localeCompare(b.name));
                result.push({
                    id: cat.id,
                    name: cat.name,
                    key: cat.key,
                    icon: cat.icon,
                    colorClass: cat.colorClass,
                    providers: items
                });
            }
        }

        return result;
    }

    getAllBypassCategories(allFeeds: string[] = [], searchQuery: string = ''): BypassCategoryGroup[] {
        const uniqueFeeds = Array.from(new Set(allFeeds.map(f => (f || '').trim()).filter(Boolean)));
        return this.groupFeedsByCategory(uniqueFeeds, searchQuery);
    }
}
