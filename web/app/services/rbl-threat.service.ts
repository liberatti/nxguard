import { Injectable } from '@angular/core';

export interface RblProviderInfo {
    name: string;
    category: string;
    categoryKey: string;
    icon: string;
    colorClass: string;
    description?: string;
}

export interface ThreatCategoryGroup {
    name: string;
    key: string;
    icon: string;
    colorClass: string;
    providers: RblProviderInfo[];
}

const KNOWN_PROVIDERS: Record<string, { category: string; icon: string; colorClass: string; description?: string }> = {
    // Tor & Anonymizers
    dan_tor_exit: { category: 'Tor Exit Nodes', icon: 'vpn_lock', colorClass: 'cat-tor', description: 'Active Tor exit relays' },
    dan_tor_all: { category: 'Tor Exit Nodes', icon: 'vpn_lock', colorClass: 'cat-tor', description: 'All Tor network nodes' },
    tor_exit: { category: 'Tor Exit Nodes', icon: 'vpn_lock', colorClass: 'cat-tor', description: 'Tor exit nodes blocklist' },
    tor_all: { category: 'Tor Exit Nodes', icon: 'vpn_lock', colorClass: 'cat-tor', description: 'Tor node addresses' },

    // Malware C2 & Botnets
    feodo_tracker: { category: 'Malware C2', icon: 'bug_report', colorClass: 'cat-malware', description: 'Feodo Trojan & Botnet C2 servers' },
    ci_bad_guys: { category: 'Malware C2', icon: 'bug_report', colorClass: 'cat-malware', description: 'Known malicious hosts & C2 nodes' },
    binarydefense: { category: 'Malware C2', icon: 'bug_report', colorClass: 'cat-malware', description: 'Binary Defense threat intel feed' },
    abuse_ch_c2: { category: 'Malware C2', icon: 'bug_report', colorClass: 'cat-malware', description: 'Abuse.ch command & control list' },

    // Brute Force & Scanning
    greensnow: { category: 'Brute Force', icon: 'lock_open', colorClass: 'cat-bruteforce', description: 'Active brute force attacks & scanning' },
    bruteforceblocker: { category: 'Brute Force', icon: 'lock_open', colorClass: 'cat-bruteforce', description: 'SSH & service brute force blocklist' },
    blocklist_de: { category: 'Brute Force', icon: 'lock_open', colorClass: 'cat-bruteforce', description: 'Fail2ban reported attacks & brute force' },

    // Web Attacks & Exploits
    'cruzit web attacks': { category: 'Web Attacks', icon: 'web', colorClass: 'cat-web', description: 'Web application exploits & crawlers' },
    cruzit_web_attacks: { category: 'Web Attacks', icon: 'web', colorClass: 'cat-web', description: 'Web application exploits & crawlers' },
    dshield: { category: 'Web Attacks', icon: 'security_update_warning', colorClass: 'cat-web', description: 'SANS Internet Storm Center top attackers' },

    // Spam & Bogons
    spamhaus_drop: { category: 'Spam & Bogons', icon: 'mark_email_unread', colorClass: 'cat-spam', description: 'Spamhaus Don\'t Route Or Peer list' },
    spamhaus_edrop: { category: 'Spam & Bogons', icon: 'mark_email_unread', colorClass: 'cat-spam', description: 'Spamhaus Extended DROP list' },
    cymru_bogons: { category: 'Spam & Bogons', icon: 'alt_route', colorClass: 'cat-spam', description: 'Team Cymru unallocated & bogon IP space' },

    // Compromised & SSL Abuse
    et_compromised: { category: 'Compromised Hosts', icon: 'gpp_bad', colorClass: 'cat-compromised', description: 'Emerging Threats compromised host list' },
    sslbl_abuse_ch: { category: 'Compromised Hosts', icon: 'gpp_bad', colorClass: 'cat-compromised', description: 'SSL Blacklist malicious certificates' },

    // Threat Intelligence
    firehol_level1: { category: 'Threat Intel', icon: 'shield', colorClass: 'cat-intel', description: 'FireHOL verified high-risk attackers' },
    talos_intel: { category: 'Threat Intel', icon: 'shield', colorClass: 'cat-intel', description: 'Cisco Talos threat intelligence feed' }
};

const CATEGORY_KEYS: Record<string, string> = {
    'Tor Exit Nodes': 'THREAT_CATEGORY.TOR_EXIT_NODES',
    'Malware C2': 'THREAT_CATEGORY.MALWARE_C2',
    'Brute Force': 'THREAT_CATEGORY.BRUTE_FORCE',
    'Web Attacks': 'THREAT_CATEGORY.WEB_ATTACKS',
    'Compromised Hosts': 'THREAT_CATEGORY.COMPROMISED_HOSTS',
    'Spam & Bogons': 'THREAT_CATEGORY.SPAM_BOGONS',
    'Threat Intel': 'THREAT_CATEGORY.THREAT_INTEL'
};

const CATEGORY_ORDER = [
    { name: 'Tor Exit Nodes', key: 'THREAT_CATEGORY.TOR_EXIT_NODES', icon: 'vpn_lock', colorClass: 'cat-tor' },
    { name: 'Malware C2', key: 'THREAT_CATEGORY.MALWARE_C2', icon: 'bug_report', colorClass: 'cat-malware' },
    { name: 'Brute Force', key: 'THREAT_CATEGORY.BRUTE_FORCE', icon: 'lock_open', colorClass: 'cat-bruteforce' },
    { name: 'Web Attacks', key: 'THREAT_CATEGORY.WEB_ATTACKS', icon: 'web', colorClass: 'cat-web' },
    { name: 'Compromised Hosts', key: 'THREAT_CATEGORY.COMPROMISED_HOSTS', icon: 'gpp_bad', colorClass: 'cat-compromised' },
    { name: 'Spam & Bogons', key: 'THREAT_CATEGORY.SPAM_BOGONS', icon: 'mark_email_unread', colorClass: 'cat-spam' },
    { name: 'Threat Intel', key: 'THREAT_CATEGORY.THREAT_INTEL', icon: 'shield', colorClass: 'cat-intel' }
];

@Injectable({
    providedIn: 'root'
})
export class RblThreatService {

    getProviderInfo(providerName: string): RblProviderInfo {
        const cleanName = (providerName || '').trim();
        const lower = cleanName.toLowerCase();
        const entry = KNOWN_PROVIDERS[lower] || KNOWN_PROVIDERS[cleanName];

        if (entry) {
            return {
                name: cleanName,
                category: entry.category,
                categoryKey: CATEGORY_KEYS[entry.category] || 'THREAT_CATEGORY.THREAT_INTEL',
                icon: entry.icon,
                colorClass: entry.colorClass,
                description: entry.description
            };
        }

        // Heuristic detection based on keyword
        let category = 'Threat Intel';
        let icon = 'shield';
        let colorClass = 'cat-intel';

        if (lower.includes('tor') || lower.includes('exit') || lower.includes('proxy')) {
            category = 'Tor Exit Nodes';
            icon = 'vpn_lock';
            colorClass = 'cat-tor';
        } else if (lower.includes('malware') || lower.includes('c2') || lower.includes('feodo') || lower.includes('bot')) {
            category = 'Malware C2';
            icon = 'bug_report';
            colorClass = 'cat-malware';
        } else if (lower.includes('brute') || lower.includes('force') || lower.includes('greensnow')) {
            category = 'Brute Force';
            icon = 'lock_open';
            colorClass = 'cat-bruteforce';
        } else if (lower.includes('web') || lower.includes('attack') || lower.includes('dshield')) {
            category = 'Web Attacks';
            icon = 'web';
            colorClass = 'cat-web';
        } else if (lower.includes('spam') || lower.includes('bogon') || lower.includes('drop')) {
            category = 'Spam & Bogons';
            icon = 'mark_email_unread';
            colorClass = 'cat-spam';
        } else if (lower.includes('compromised') || lower.includes('ssl') || lower.includes('abuse')) {
            category = 'Compromised Hosts';
            icon = 'gpp_bad';
            colorClass = 'cat-compromised';
        }

        return {
            name: cleanName,
            category,
            categoryKey: CATEGORY_KEYS[category] || 'THREAT_CATEGORY.THREAT_INTEL',
            icon,
            colorClass
        };
    }

    groupProvidersByCategory(providers: string[], searchQuery: string = ''): ThreatCategoryGroup[] {
        if (!providers || providers.length === 0) {
            return [];
        }

        const query = (searchQuery || '').trim().toLowerCase();
        const seen = new Set<string>();
        const list: RblProviderInfo[] = [];

        for (const p of providers) {
            if (!p || seen.has(p)) continue;
            seen.add(p);
            const info = this.getProviderInfo(p);

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

        const groupsMap = new Map<string, RblProviderInfo[]>();
        for (const cat of CATEGORY_ORDER) {
            groupsMap.set(cat.name, []);
        }

        for (const item of list) {
            const current = groupsMap.get(item.category) || [];
            current.push(item);
            groupsMap.set(item.category, current);
        }

        const result: ThreatCategoryGroup[] = [];
        for (const cat of CATEGORY_ORDER) {
            const items = groupsMap.get(cat.name) || [];
            if (items.length > 0) {
                items.sort((a, b) => a.name.localeCompare(b.name));
                result.push({
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
}
