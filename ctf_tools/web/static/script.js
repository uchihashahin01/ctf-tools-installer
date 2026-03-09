const socket = io();
const categoryList = document.getElementById('category-list');
const toolsGrid = document.getElementById('tools-grid');
const manualPage = document.getElementById('manual-page');
const terminal = document.getElementById('terminal-output');
const statusIndicator = document.getElementById('connection-status');
const pageTitle = document.getElementById('page-title');

let currentCategory = null;

// --- Update check ---
async function checkForUpdate() {
    try {
        const res = await fetch('/api/check-update');
        const data = await res.json();
        if (data.update_available) {
            const banner = document.getElementById('update-banner');
            const text = document.getElementById('update-text');
            text.textContent = `Update available: v${data.current} \u2192 v${data.latest}  |  Run: sudo ctforge update`;
            banner.classList.remove('hidden');
        }
    } catch (e) { /* silent */ }
}

// --- Socket Events ---
socket.on('connect', () => {
    statusIndicator.textContent = 'Connected';
    statusIndicator.classList.add('connected');
    log('Connected to server.', 'info');
});

socket.on('disconnect', () => {
    statusIndicator.textContent = 'Disconnected';
    statusIndicator.classList.remove('connected');
    log('Disconnected from server.', 'error');
});

socket.on('log_message', (data) => {
    log(data.message, data.status.toLowerCase());
});

socket.on('install_start', (data) => {
    log(`Starting operation for: ${data.target}`, 'header');
});

socket.on('install_complete', (data) => {
    if (data.status === 'success') {
        log(`Operation completed for: ${data.target}`, 'success');
        if (currentCategory) loadTools(currentCategory.id);
    } else {
        log(`Operation failed for: ${data.target}`, 'error');
    }
});

// --- Navigation helpers ---

function showToolsView() {
    toolsGrid.classList.remove('hidden');
    manualPage.classList.add('hidden');
    const actions = document.getElementById('category-actions');
    if (actions) actions.classList.remove('hidden');
}

function showManualView() {
    toolsGrid.classList.add('hidden');
    manualPage.classList.remove('hidden');
    const actions = document.getElementById('category-actions');
    if (actions) actions.classList.add('hidden');
}

// --- UI Logic ---

async function loadCategories() {
    const res = await fetch('/api/categories');
    const categories = await res.json();
    categoryList.innerHTML = '';
    categories.forEach(cat => {
        const li = document.createElement('li');
        li.textContent = cat.name.toUpperCase();
        li.dataset.id = cat.id;
        li.onclick = () => selectCategory(li, cat);
        categoryList.appendChild(li);
    });
}

function clearSidebarActive() {
    document.querySelectorAll('.sidebar li').forEach(el => el.classList.remove('active'));
}

function selectCategory(element, category) {
    clearSidebarActive();
    element.classList.add('active');
    currentCategory = category;
    pageTitle.textContent = category.name + " Tools";
    showToolsView();
    loadTools(category.id);
}

async function showManual() {
    clearSidebarActive();
    document.getElementById('nav-manual').classList.add('active');
    currentCategory = null;
    pageTitle.textContent = "Manual Installation Guide";
    showManualView();
    await loadManual();
}

async function loadManual() {
    manualPage.innerHTML = '<div class="placeholder-msg">Loading manual\u2026</div>';
    try {
        const res = await fetch('/api/manual');
        const data = await res.json();
        let html = '<div class="manual-intro">Copy-paste these commands to install tools manually on Ubuntu/Debian.</div>';
        for (const [catId, commands] of Object.entries(data)) {
            html += `<div class="manual-category">
                <h2>${catId.charAt(0).toUpperCase() + catId.slice(1)}</h2>
                <table class="manual-table">
                    <thead><tr><th>Tool</th><th>Command</th></tr></thead>
                    <tbody>`;
            for (const item of commands) {
                const escaped = item.command.replace(/</g, '&lt;').replace(/>/g, '&gt;');
                html += `<tr>
                    <td>${item.tool}</td>
                    <td><code class="cmd-code" onclick="copyCmd(this)">${escaped}</code>
                        <span class="copy-hint">click to copy</span></td>
                </tr>`;
            }
            html += '</tbody></table></div>';
        }
        manualPage.innerHTML = html;
    } catch (e) {
        manualPage.innerHTML = '<div class="placeholder-msg">Failed to load manual.</div>';
    }
}

function copyCmd(el) {
    navigator.clipboard.writeText(el.textContent).then(() => {
        const hint = el.nextElementSibling;
        if (hint) { hint.textContent = 'copied!'; setTimeout(() => { hint.textContent = 'click to copy'; }, 1200); }
    });
}

async function loadTools(categoryId) {
    toolsGrid.innerHTML = '<div class="placeholder-msg">Loading tools\u2026</div>';
    const res = await fetch(`/api/tools/${categoryId}`);
    const tools = await res.json();
    toolsGrid.innerHTML = '';

    let headerContainer = document.getElementById('category-actions');
    if (!headerContainer) {
        headerContainer = document.createElement('div');
        headerContainer.id = 'category-actions';
        headerContainer.style.width = '100%';
        headerContainer.style.marginBottom = '20px';
        toolsGrid.parentNode.insertBefore(headerContainer, toolsGrid);
    }
    headerContainer.classList.remove('hidden');
    headerContainer.innerHTML = `
        <button class="install-all-btn" onclick="installCategory('${categoryId}')">INSTALL ALL ${categoryId.toUpperCase()}</button>
        <button class="nuke-btn" onclick="nukeSystem()">\u2622 NUKE ALL</button>
    `;

    tools.forEach(tool => {
        const card = document.createElement('div');
        card.className = 'card';
        if (tool.installed) card.classList.add('installed');

        let statusClass = '';
        if (tool.health === 'healthy') statusClass = 'healthy';
        else if (tool.health === 'installed_but_error') statusClass = 'broken';

        let statusText = tool.installed ? 'Installed' : 'Click to install';
        card.innerHTML = `
            <h3><span class="status-light ${statusClass}"></span>${tool.name}</h3>
            <span class="type-badge">${tool.type}</span>
            <p>${statusText}</p>
        `;
        card.onclick = () => installTool(tool);

        if (tool.installed) {
            const uninstallBtn = document.createElement('button');
            uninstallBtn.innerText = '\ud83d\uddd1\ufe0f';
            uninstallBtn.title = 'Uninstall';
            uninstallBtn.style.cssText = 'position:absolute;top:12px;right:10px;background:transparent;border:none;cursor:pointer;font-size:1.1rem;z-index:10;';
            uninstallBtn.onclick = (e) => { e.stopPropagation(); uninstallTool(tool); };
            card.appendChild(uninstallBtn);
        }
        toolsGrid.appendChild(card);
    });
}

async function installCategory(categoryId) {
    if (!confirm(`Install ALL ${categoryId} tools?`)) return;
    log(`Installing all ${categoryId} tools\u2026`);
    await fetch(`/api/install/category/${categoryId}`, { method: 'POST' });
}

async function installTool(tool) {
    log(`Installing ${tool.name}\u2026`);
    await fetch('/api/install/tool', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tool)
    });
}

async function uninstallTool(tool) {
    if (!confirm(`Uninstall ${tool.name}?`)) return;
    log(`Uninstalling ${tool.name}\u2026`);
    await fetch('/api/uninstall/tool', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tool)
    });
}

async function nukeSystem() {
    if (!confirm("WARNING: Uninstall ALL tools?")) return;
    if (!confirm("Are you absolutely sure?")) return;
    log('INITIATING SYSTEM NUKE\u2026');
    await fetch('/api/nuke', { method: 'POST' });
}

function log(message, type = 'info') {
    const line = document.createElement('div');
    line.className = `log-line ${type}`;
    line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
}

document.getElementById('clear-log').onclick = () => { terminal.innerHTML = ''; };

// Init
loadCategories();
checkForUpdate();
