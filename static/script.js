const socket = io();
const categoryList = document.getElementById('category-list');
const toolsGrid = document.getElementById('tools-grid');
const terminal = document.getElementById('terminal-output');
const statusIndicator = document.getElementById('connection-status');
const pageTitle = document.getElementById('page-title');

let currentCategory = null;

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
    log(`Starting installation for: ${data.target}`, 'header');
});

socket.on('install_complete', (data) => {
    if (data.status === 'success') {
        log(`Operation completed for: ${data.target}`, 'success');
        // Refresh the UI to reflect changes (green/red status)
        if (currentCategory) {
            // Re-fetch the tools for the current category without full reload
            loadTools(currentCategory.id);
        }
    } else {
        log(`Operation failed for: ${data.target}`, 'error');
    }
});

// --- UI Logic ---

async function loadCategories() {
    const res = await fetch('/api/categories');
    const categories = await res.json();

    categoryList.innerHTML = '';

    categories.forEach(cat => {
        const li = document.createElement('li');
        li.textContent = cat.name.toUpperCase();
        li.dataset.id = cat.id;
        li.onclick = () => {
            selectCategory(li, cat);
        };
        categoryList.appendChild(li);
    });
}

function selectCategory(element, category) {
    // Highlight sidebar
    document.querySelectorAll('.sidebar li').forEach(el => el.classList.remove('active'));
    element.classList.add('active');

    currentCategory = category;
    pageTitle.textContent = category.name + " Tools";
    loadTools(category.id);
}

async function loadTools(categoryId) {
    toolsGrid.innerHTML = '<div class="placeholder-msg">Loading tools...</div>';

    // Fetch tools
    const res = await fetch(`/api/tools/${categoryId}`);
    const tools = await res.json();

    toolsGrid.innerHTML = '';

    // Header Actions Container
    let headerContainer = document.getElementById('category-actions');
    if (!headerContainer) {
        headerContainer = document.createElement('div');
        headerContainer.id = 'category-actions';
        headerContainer.style.width = '100%';
        headerContainer.style.marginBottom = '20px';
        toolsGrid.parentNode.insertBefore(headerContainer, toolsGrid);
    }

    headerContainer.innerHTML = `
        <button class="install-all-btn" onclick="installCategory('${categoryId}')">INSTALL ALL ${categoryId.toUpperCase()} TOOLS</button>
        <button class="nuke-btn" onclick="nukeSystem()">☢️ NUKE SYSTEM (Uninstall All)</button>
    `;

    tools.forEach(tool => {
        const card = document.createElement('div');
        card.className = 'card';
        if (tool.installed) {
            card.classList.add('installed');
        }

        // Define status light class
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

        // Add a small uninstall button if installed
        if (tool.installed) {
            const uninstallBtn = document.createElement('button');
            uninstallBtn.innerText = '🗑️';
            uninstallBtn.title = 'Uninstall';
            // Inline styles for the trash button since it's a small dynamic element
            uninstallBtn.style.cssText = 'position:absolute; top:12px; right:10px; background:transparent; border:none; cursor:pointer; font-size: 1.1rem; z-index:10;';
            uninstallBtn.onclick = (e) => {
                e.stopPropagation(); // Prevent card click
                uninstallTool(tool);
            };
            card.appendChild(uninstallBtn);
        }

        toolsGrid.appendChild(card);
    });
}

async function installCategory(categoryId) {
    if (!confirm(`Install ALL ${categoryId} tools? This may take a while.`)) return;
    log(`Sending request to install all in ${categoryId}...`);
    await fetch(`/api/install/category/${categoryId}`, { method: 'POST' });
}

async function installTool(tool) {
    log(`Sending request to install ${tool.name}...`);
    await fetch('/api/install/tool', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tool)
    });
}

async function uninstallTool(tool) {
    if (!confirm(`Are you sure you want to uninstall ${tool.name}?`)) return;

    log(`Sending request to uninstall ${tool.name}...`);
    await fetch('/api/uninstall/tool', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tool)
    });
}

async function nukeSystem() {
    if (!confirm("WARNING: This will try to uninstall ALL tools managed by this dashboard. Are you sure?")) return;
    if (!confirm("DOUBLE CHECK: Use this only for testing/cleanup. Proceed?")) return;

    log(`INITIATING SYSTEM NUKE...`);
    await fetch('/api/nuke', { method: 'POST' });
}

function log(message, type = 'info') {
    const line = document.createElement('div');
    line.className = `log-line ${type}`;
    line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
}

document.getElementById('clear-log').onclick = () => {
    terminal.innerHTML = '';
};

// Init
loadCategories();
