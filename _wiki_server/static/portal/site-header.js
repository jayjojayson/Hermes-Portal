/* Hermes Portal – Shared site header.
   - Theme-Bootstrap (sofort, ohne defer)
   - Renders unified glassy header markup at <div id="site-header"></div>
   - Renders sidebar (≥1280px) with quick-nav + zuletzt besucht
   - Setzt active Nav-Item basierend auf body[data-page]
   - Brand-Name wird via window.HP_BRAND / window.HP_PORTAL_NAME aus base.html gesetzt.
*/
(function() {
    'use strict';

    var THEME_KEY  = 'theme';
    var RECENT_KEY = 'jtw_recent_pages';

    // ---- Theme helpers (run immediately) ---------------------------
    function getStoredTheme() {
        try { return localStorage.getItem(THEME_KEY); } catch (e) { return null; }
    }
    function preferredTheme() {
        var stored = getStoredTheme();
        if (stored === 'dark' || stored === 'light') return stored;
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) return 'light';
        return 'dark';
    }
    function applyTheme(t) {
        document.documentElement.setAttribute('data-theme', t);
        if (document.body) document.body.setAttribute('data-theme', t);
        var btn = document.querySelector('.site-header .theme-toggle');
        if (btn) btn.textContent = t === 'dark' ? '☀️' : '🌙';
    }
    var initialTheme = preferredTheme();
    applyTheme(initialTheme);

    function toggleTheme() {
        var current = document.documentElement.getAttribute('data-theme') || 'dark';
        var next = current === 'dark' ? 'light' : 'dark';
        try { localStorage.setItem(THEME_KEY, next); } catch (e) {}
        applyTheme(next);
    }
    window.toggleTheme = toggleTheme;

    // ---- Article expand (used in news posts) -------------------------
    window.toggleArticle = function(btn) {
        var item = btn.closest('.news-item');
        if (!item) return;
        var full = item.querySelector('.news-full');
        if (!full) return;
        var open = full.classList.toggle('open');
        btn.textContent = open ? 'Weniger anzeigen' : 'Weiterlesen';
    };

    // ---- Nav configuration -------------------------------------------
    var NAV_ALL = [
        { key: 'dashboard',label: 'Dashboard',href: '/',                          icon: '🏠' },
        { key: 'wiki',     label: 'Wiki',     href: '/wiki/',                     icon: '📚' },
        { key: 'news',     label: 'News',     href: '/blog/',                     icon: '📰' },
        { key: 'briefing', label: 'Briefing', href: '/briefing/',                 icon: '☕' },
        { key: 'aufgaben', label: 'Aufgaben', href: '/blog/aufgaben.html',        icon: '✅' },
        { key: 'explorer', label: 'Explorer', href: '/explorer/',                 icon: '📂' },
        { key: 'chat',     label: 'Chat',     href: '/chat/',                     icon: '💬' },
        { key: 'activity', label: 'Aktivität',href: '/activity/',                 icon: '⚡' },
        { key: 'settings', label: 'Settings', href: '/settings/',                 icon: '⚙️' }
    ];
    // HA-Ingress-Prefix (leerer String, wenn standalone)
    var INGRESS = (typeof window !== 'undefined' && window.HP_INGRESS_PATH) || '';
    function withPrefix(p) { return INGRESS + p; }

    // Filter + Ingress-Prefix anwenden.
    // Respektiert window.HP_NAV_HIDE = { news: true, briefing: true }
    function navItems() {
        var hide = window.HP_NAV_HIDE || {};
        return NAV_ALL.filter(function(item) {
            return !hide[item.key];
        }).map(function(item) {
            return { key: item.key, label: item.label, icon: item.icon, href: withPrefix(item.href) };
        });
    }
    // Legacy-Alias für Stellen, die NAV als Top-Level-Konstante nutzten
    var NAV = NAV_ALL;

    // Wiki-only pages (for sidebar etc.)
    var WIKI_PAGES = { wiki: 1, 'wiki-page': 1, 'wiki-edit': 1, 'wiki-new': 1, 'wiki-search': 1, 'wiki-tags': 1 };

    // ---- Recent pages (localStorage) ---------------------------------
    function getRecent() {
        try {
            var raw = localStorage.getItem(RECENT_KEY);
            if (!raw) return [];
            var arr = JSON.parse(raw);
            return Array.isArray(arr) ? arr : [];
        } catch (e) { return []; }
    }
    function pushRecent() {
        // Nur sinnvolle Seiten in den Recent-Track; nicht jede static-Datei.
        // Unter HA-Ingress liegt der Pfad als /api/hassio_ingress/TOKEN/... vor —
        // den Prefix abziehen, damit die Vergleiche ('/', '/wiki/' etc.) greifen.
        var rawPath = location.pathname;
        var path = (INGRESS && rawPath.indexOf(INGRESS) === 0)
                    ? (rawPath.slice(INGRESS.length) || '/')
                    : rawPath;
        var title = (document.title || path).replace(/\s+[–—\-]\s+.*$/i, '');
        // Skip blog list/index pages (zu viele, zu generisch)
        if (path === '/' || /\/blog\/?$/.test(path) || /\/blog\/page\d+\.html$/.test(path)) return;
        if (path === '/wiki' || path === '/wiki/') return;
        if (path === '/activity' || path === '/activity/') return;
        if (path === '/settings/' || /^\/settings\/?/.test(path)) return;
        if (path === '/new' || path === '/search' || path === '/tags') return;
        try {
            var arr = getRecent();
            // Remove existing entry with same path
            arr = arr.filter(function(e) { return e.path !== path; });
            arr.unshift({ path: path, title: title, ts: Date.now() });
            arr = arr.slice(0, 5);
            localStorage.setItem(RECENT_KEY, JSON.stringify(arr));
        } catch (e) {}
    }

    // ---- Build markup -------------------------------------------------
    function buildHeader(activeKey) {
        var navHtml = navItems().map(function(item) {
            var cls = (item.key === activeKey) ? ' class="active"' : '';
            return '<a href="' + item.href + '"' + cls + '>' + item.label + '</a>';
        }).join('');

        var themeIcon = (document.documentElement.getAttribute('data-theme') === 'dark') ? '☀️' : '🌙';

        var brand = (window.HP_BRAND || window.HP_PORTAL_NAME || 'Hermes Portal');
        return (
            '<div class="header-logo" title="' + brand + '">' +
              '<img class="brand-logo" src="' + withPrefix('/static/portal/logo.png') + '" alt="" aria-hidden="true">' +
              '<span class="live-dot" aria-hidden="true"></span>' +
              '<span>' + brand + '</span>' +
            '</div>' +
            '<nav class="nav">' + navHtml + '</nav>' +
            '<div class="header-right">' +
              '<button type="button" onclick="toggleTheme()" class="theme-toggle" aria-label="Theme umschalten" title="Theme umschalten">' +
                themeIcon +
              '</button>' +
            '</div>'
        );
    }

    function buildSidebar(activeKey) {
        var navHtml = navItems().map(function(item) {
            var cls = (item.key === activeKey) ? 'sb-link active' : 'sb-link';
            return '<a href="' + item.href + '" class="' + cls + '">' +
                       '<span class="ico">' + item.icon + '</span>' +
                       '<span>' + item.label + '</span>' +
                   '</a>';
        }).join('');

        var recent = getRecent();
        var recentHtml = '';
        if (recent.length === 0) {
            recentHtml = '<div class="sb-empty">— noch keine —</div>';
        } else {
            recentHtml = recent.map(function(r) {
                var label = (r.title || r.path).slice(0, 32);
                return '<a class="sb-recent" href="' + r.path + '" title="' + (r.title || '').replace(/"/g, '&quot;') + '">' +
                           label +
                       '</a>';
            }).join('');
        }

        var version = (window.HP_VERSION || '');
        var versionFooter = version
            ? '<div class="sb-version" title="Hermes Portal Version">' +
                '<a href="https://github.com/jayjojayson/Hermes-Portal/releases/tag/v' + version + '" ' +
                'target="_blank" rel="noopener">v' + version + '</a>' +
                '<span id="sb-update-badge" hidden></span>' +
              '</div>'
            : '';
        return (
            '<div class="sb-group">' +
              '<div class="sb-label">Panel</div>' +
              navHtml +
            '</div>' +
            '<div class="sb-group">' +
              '<div class="sb-label">Zuletzt</div>' +
              recentHtml +
            '</div>' +
            versionFooter
        );
    }

    // ---- Sidebar toggle (separate state for dashboard vs. rest) ----
    var SIDEBAR_KEY_DB = 'wiki_sidebar_db_v2';
    var SIDEBAR_KEY_OT = 'wiki_sidebar_ot_v2';

    function isDashboardPage() {
        var p = location.pathname;
        return p === '/' || p === '';
    }

    function getSidebarState() {
        try {
            var key = isDashboardPage() ? SIDEBAR_KEY_DB : SIDEBAR_KEY_OT;
            return localStorage.getItem(key);
        } catch (e) { return null; }
    }

    function setSidebarState(open) {
        try {
            var key = isDashboardPage() ? SIDEBAR_KEY_DB : SIDEBAR_KEY_OT;
            localStorage.setItem(key, open ? 'open' : 'closed');
        } catch (e) {}
    }

    function sidebarDefault() {
        // Dashboard = open, everything else = closed
        return isDashboardPage() ? 'open' : 'closed';
    }

    function toggleSidebar() {
        var sb = document.getElementById('site-sidebar');
        if (!sb) return;
        var isCollapsed = sb.classList.contains('collapsed');
        sb.classList.toggle('collapsed');
        document.body.classList.toggle('collapsed');
        // isCollapsed is the state BEFORE toggle:
        //   was collapsed → now open → save open=true
        //   was open → now collapsed → save open=false
        setSidebarState(isCollapsed);

        // Update button icon
        var btn = document.getElementById('sidebar-toggle');
        if (btn) {
            btn.innerHTML = !isCollapsed ? '◀' : '▶';
        }

        // Show/hide hover strip
        var strip = document.getElementById('sidebar-hover-strip');
        if (strip) {
            strip.style.display = !isCollapsed ? 'none' : 'block';
        }
    }

    function openSidebar() {
        var sb = document.getElementById('site-sidebar');
        if (!sb || !sb.classList.contains('collapsed')) return;
        sb.classList.remove('collapsed');
        document.body.classList.remove('collapsed');
        setSidebarState(true);
        var btn = document.getElementById('sidebar-toggle');
        if (btn) btn.innerHTML = '◀';
        var strip = document.getElementById('sidebar-hover-strip');
        if (strip) strip.style.display = 'none';
    }

    function determineActive() {
        var explicit = document.body && document.body.getAttribute('data-page');
        if (explicit) return explicit;
        var p = location.pathname;
        if (p === '/') return 'dashboard';
        if (p.indexOf('/wiki') === 0 || p.indexOf('/entity/') === 0 || p.indexOf('/concept/') === 0 ||
            p.indexOf('/edit/') === 0 || p === '/new' || p === '/search' || p === '/tags') {
            return 'wiki';
        }
        if (p.indexOf('/activity') === 0) return 'activity';
        if (p.indexOf('/explorer') === 0) return 'explorer';
        if (p.indexOf('/briefing') === 0) return 'briefing';
        if (p.indexOf('/blog/briefing') >= 0) return 'briefing';
        if (p.indexOf('/blog/aufgaben') >= 0) return 'aufgaben';
        if (p.indexOf('/blog/categories') >= 0 || p.indexOf('/blog/category-') >= 0) return 'news';
        if (p.indexOf('/settings') === 0) return 'settings';
        if (p.indexOf('/blog/anleitung') >= 0) return 'news';
        if (p.indexOf('/blog') >= 0) return 'news';
        return '';
    }

    function render() {
        var active = determineActive();
        var activeForNav = (active && active.indexOf('wiki') === 0) ? 'wiki' : active;
        var html = buildHeader(activeForNav);

        // ---- Header placeholder
        var placeholder = document.getElementById('site-header');
        if (!placeholder) {
            placeholder = document.createElement('header');
            placeholder.id = 'site-header';
            document.body.insertBefore(placeholder, document.body.firstChild);
        }
        if (placeholder.tagName.toLowerCase() !== 'header') {
            var hdr = document.createElement('header');
            hdr.id = 'site-header';
            placeholder.parentNode.replaceChild(hdr, placeholder);
            placeholder = hdr;
        }
        placeholder.className = 'site-header';
        placeholder.innerHTML = html;

        // ---- Sidebar (always injected; CSS hides it below 1280px)
        var sb = document.getElementById('site-sidebar');
        if (!sb) {
            sb = document.createElement('aside');
            sb.id = 'site-sidebar';
            sb.className = 'site-sidebar';
            // Sidebar nach dem Header in den Body
            placeholder.parentNode.insertBefore(sb, placeholder.nextSibling);
        }
        document.body.classList.add('has-sidebar');

        // ---- Sidebar content wrapper (so toggle button survives re-renders)
        var sbContent = document.getElementById('sidebar-content');
        if (!sbContent) {
            sbContent = document.createElement('div');
            sbContent.id = 'sidebar-content';
            sb.appendChild(sbContent);
        }
        sbContent.innerHTML = buildSidebar(activeForNav);

        // ---- Sidebar toggle button (right-aligned in Panel label)
        // Always re-position after sbContent re-render
        var firstLabel = sb.querySelector('#sidebar-content .sb-label');
        if (firstLabel) {
            firstLabel.style.display = 'flex';
            firstLabel.style.justifyContent = 'space-between';
            firstLabel.style.alignItems = 'center';
        }
        var toggleBtn = document.getElementById('sidebar-toggle');
        if (!toggleBtn) {
            toggleBtn = document.createElement('button');
            toggleBtn.id = 'sidebar-toggle';
            toggleBtn.className = 'sidebar-toggle-btn';
            toggleBtn.setAttribute('aria-label', 'Sidebar umschalten');
            toggleBtn.setAttribute('title', 'Sidebar ein-/ausklappen');
        }
        // Make sure button is attached to firstLabel (after re-render it may be detached)
        var currentParent = toggleBtn.parentNode;
        if (!currentParent || currentParent === sb) {
            if (firstLabel) firstLabel.appendChild(toggleBtn);
        }

        // ---- Hover strip (left edge, reopens collapsed sidebar)
        var hoverStrip = document.getElementById('sidebar-hover-strip');
        if (!hoverStrip) {
            hoverStrip = document.createElement('div');
            hoverStrip.id = 'sidebar-hover-strip';
            hoverStrip.className = 'sidebar-hover-strip';
            hoverStrip.setAttribute('title', 'Sidebar aufklappen');
            hoverStrip.addEventListener('mouseenter', openSidebar);
            document.body.appendChild(hoverStrip);
        }

        // Set initial state
        var savedState = getSidebarState();
        var shouldOpen;
        if (isDashboardPage()) {
            // Dashboard: default = open, but respect explicit close
            shouldOpen = (savedState !== 'closed');
        } else {
            // Other pages: default = closed, but respect explicit open
            shouldOpen = (savedState === 'open');
        }

        if (!shouldOpen) {
            sb.classList.add('collapsed');
            document.body.classList.add('collapsed');
            toggleBtn.innerHTML = '▶';
            hoverStrip.style.display = 'block';
        } else {
            sb.classList.remove('collapsed');
            document.body.classList.remove('collapsed');
            toggleBtn.innerHTML = '◀';
            hoverStrip.style.display = 'none';
        }
        // Attach click handler
        toggleBtn.onclick = toggleSidebar;

        // Remove legacy <header> elements
        document.querySelectorAll('body > header').forEach(function(h) {
            if (h.id !== 'site-header') h.remove();
        });
        document.querySelectorAll('header').forEach(function(h) {
            if (h.id !== 'site-header' && !h.classList.contains('site-header')) h.remove();
        });

        // Footer auf statischen Blog-Pages mit dem Portal-Footer überschreiben.
        // Erkennung: <footer> ohne class="footer" (das ist der Portal-Footer aus base.html).
        var portalName = (window.HP_PORTAL_NAME || 'Hermes Portal');
        var currentYear = new Date().getFullYear();
        var footerHtml = '<img src="' + withPrefix('/static/portal/logo.png') + '" alt="" class="footer-logo" aria-hidden="true">'
            + '<span>' + portalName + ' &copy; ' + currentYear + '</span>';
        document.querySelectorAll('footer').forEach(function(f) {
            if (f.classList.contains('footer')) return; // Portal-eigener Footer – nicht anfassen
            f.className = 'footer';
            f.innerHTML = footerHtml;
        });

        // Auf statischen Blog-Pages: .hero-links (Anleitungen/Kategorien-Buttons) ausblenden,
        // weil das Portal keine separaten Anleitungs-/Kategorienseiten ausliefert.
        document.querySelectorAll('.hero-links').forEach(function(el) {
            el.style.display = 'none';
        });

        if (document.body) document.body.setAttribute('data-theme',
            document.documentElement.getAttribute('data-theme') || 'dark');

        // Track this page in recent (after render so title is final)
        try { pushRecent(); } catch (e) {}

        // Hermes-Status polling für Live-Dot im Header
        try { startHermesStatusPolling(); } catch (e) {}

        // Update-Check (GitHub Releases) — einmalig nach Render
        try { checkForUpdate(); } catch (e) {}
    }

    // ---- Update-Check ------------------------------------------------
    function checkForUpdate() {
        fetch(withPrefix('/api/version/check'), { cache: 'no-store' })
            .then(function(r){ return r.ok ? r.json() : null; })
            .then(function(d){
                if (!d || !d.update_available) return;
                var badge = document.getElementById('sb-update-badge');
                if (!badge) return;
                badge.hidden = false;
                badge.className = 'sb-update-badge';
                badge.innerHTML = ' · <a href="' + d.url + '" target="_blank" ' +
                                  'rel="noopener" title="Neue Version verfügbar: v' +
                                  d.latest + '">⬆ v' + d.latest + '</a>';
            })
            .catch(function(){ /* offline / rate-limit — ignorieren */ });
    }

    // ---- Hermes-Status für Live-Dot ----------------------------------
    var HERMES_STATUS_STATES = ['online', 'idle', 'offline', 'unknown'];
    function applyHermesStatus(state) {
        if (HERMES_STATUS_STATES.indexOf(state) < 0) state = 'unknown';
        var dot = document.querySelector('.site-header .live-dot');
        if (!dot) return;
        HERMES_STATUS_STATES.forEach(function(s) { dot.classList.remove('status-' + s); });
        dot.classList.add('status-' + state);
        dot.title = 'Hermes: ' + state;
    }
    function pollHermesStatus() {
        fetch(withPrefix('/api/dashboard/status'), { cache: 'no-store' })
            .then(function(r) { return r.ok ? r.json() : null; })
            .then(function(d) {
                if (!d) return applyHermesStatus('unknown');
                applyHermesStatus((d.hermes || {}).state || 'unknown');
            })
            .catch(function() { applyHermesStatus('unknown'); });
    }
    var _hermesStatusInterval = null;
    function startHermesStatusPolling() {
        // Initial bewusst grau, bis erste Antwort kommt
        applyHermesStatus('unknown');
        // Erste Abfrage kurz verzögert, damit andere Page-Loads nicht behindert werden
        setTimeout(pollHermesStatus, 600);
        if (_hermesStatusInterval) clearInterval(_hermesStatusInterval);
        // alle 30s neu pollen — selbe Frequenz wie Dashboard
        _hermesStatusInterval = setInterval(pollHermesStatus, 30000);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', render);
    } else {
        render();
    }
})();
