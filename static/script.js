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
        log(`Installation completed for: ${data.target}`, 'success');
    } else {
        log(`Installation failed for: ${data.target}`, 'error');
    }
});

// --- UI Logic ---

async function loadCategories() {
    const res = await fetch('/api/categories');
    const categories = await res.json();

    categoryList.innerHTML = '';

    // "All" item
    /*
    const allLi = document.createElement('li');
    allLi.textContent = 'ALL TOOLS';
    allLi.onclick = () => loadTools('all');
    categoryList.appendChild(allLi);
    */

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

    // Install all button
    const installAllBtn = document.createElement('button');
    installAllBtn.className = 'install-all-btn';
    installAllBtn.textContent = `INSTALL ALL ${categoryId.toUpperCase()} TOOLS`;
    installAllBtn.onclick = () => installCategory(categoryId);

    // Fetch tools
    const res = await fetch(`/api/tools/${categoryId}`);
    const tools = await res.json();

    toolsGrid.innerHTML = '';

    // Insert button first (in a full width container or just separate)
    // For grid layout, we might want to put this above the grid or as a special card.
    // Let's put it above the grid in the DOM, but for now just appending to main-content cleared area?
    // Actually simplicity: Put it in the grid header area? No.
    // Let's append to main-content by clearing toolsGrid and re-adding.
    // We'll just put it inside the grid as a special wide card? No.

    // To keep it simple, we will just have the grid contain cards.
    // We can put the install button in the header? Nospace there.
    // Let's create a container above the grid.
    let headerContainer = document.getElementById('category-actions');
    if (!headerContainer) {
        headerContainer = document.createElement('div');
        headerContainer.id = 'category-actions';
        headerContainer.style.marginBottom = '20px';
        toolsGrid.parentNode.insertBefore(headerContainer, toolsGrid);
    }
    headerContainer.innerHTML = '';
    headerContainer.appendChild(installAllBtn);

    tools.forEach(tool => {
        const card = document.createElement('div');
        card.className = 'card';
        if (tool.installed) {
            card.classList.add('installed');
        }

        let statusText = tool.installed ? 'Installed' : 'Click to install';

        card.innerHTML = `
            <h3>${tool.name}</h3>
            <span class="type-badge">${tool.type}</span>
            <p>${statusText}</p>
        `;
        card.onclick = () => installTool(tool);
        toolsGrid.appendChild(card);
    });
}

async function installCategory(categoryId) {
    if (!confirm(`Install ALL ${categoryId} tools? This may take a while.`)) return;

    await fetch(`/api/install/category/${categoryId}`, { method: 'POST' });
}

async function installTool(tool) {
    // if (!confirm(`Install ${tool.name}?`)) return;

    await fetch('/api/install/tool', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tool)
    });
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
