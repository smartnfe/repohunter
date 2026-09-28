// ===== RepoHunter App =====

const API_BASE = ''; // Relative to current page
let allRepos = [];
let filteredRepos = [];

// Category mapping based on repo description/name
function getCategory(repo) {
    const name = (repo.full_name + ' ' + repo.description).toLowerCase();
    const ai = ['ai', 'machine learning', 'deep learning', 'nlp', 'llm', 'gpt', 'openai', 'anthropic', 'claude', 'agent', 'huggingface'];
    const automation = ['automation', 'automation', 'workflow', 'n8n', 'comfyui', 'rpa', 'bot'];
    const trading = ['trading', 'stock', 'forex', 'crypto', 'finance', 'money', 'bot trade'];
    const tool = ['tool', 'editor', 'ide', 'cli', 'dashboard', 'server', 'database', 'devops', 'docker', 'kubernetes'];
    
    for (const keyword of ai) {
        if (name.includes(keyword)) return 'ai';
    }
    for (const keyword of automation) {
        if (name.includes(keyword)) return 'automation';
    }
    for (const keyword of trading) {
        if (name.includes(keyword)) return 'trading';
    }
    for (const keyword of tool) {
        if (name.includes(keyword)) return 'tool';
    }
    return 'tool';
}

const categoryLabels = {
    ai: '🤖 AI',
    automation: '⚡ Automation',
    trading: '📈 Trading',
    tool: '🛠 Tools'
};

// Fetch repos data
async function fetchRepos() {
    try {
        const response = await fetch('/data/repos.json');
        if (!response.ok) throw new Error('Failed to fetch');
        allRepos = await response.json();
        filteredRepos = [...allRepos];
        updateStats();
        renderRepos();
    } catch (error) {
        console.error('Error fetching repos:', error);
        document.getElementById('repo-grid').innerHTML = 
            '<div class="empty-state"><p>❌ ไม่สามารถโหลดข้อมูล repo ได้</p></div>';
    }
}

// Update stats
function updateStats() {
    const total = filteredRepos.length;
    const totalStars = filteredRepos.reduce((sum, r) => sum + (r.stargazers_count || 0), 0);
    
    document.getElementById('total-repos').textContent = total;
    document.getElementById('total-stars').textContent = totalStars.toLocaleString();
    
    // Update last update time from JSON metadata
    const meta = allRepos._meta || {};
    const lastUpdate = meta.last_update || new Date().toLocaleDateString('th-TH');
    document.getElementById('last-update').textContent = lastUpdate;
}

// Render repo cards
function renderRepos() {
    const grid = document.getElementById('repo-grid');
    const emptyState = document.getElementById('empty-state');
    
    if (filteredRepos.length === 0) {
        grid.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }
    
    emptyState.style.display = 'none';
    
    grid.innerHTML = filteredRepos.map(repo => {
        const category = getCategory(repo);
        const lang = repo.language || '-';
        const stars = (repo.stargazers_count || 0).toLocaleString();
        const forks = (repo.forks_count || 0).toLocaleString();
        const desc = repo.description || 'ไม่มีคำอธิบาย';
        const name = repo.full_name;
        
        return `
        <div class="repo-card" data-category="${category}" data-name="${name.toLowerCase()}" data-stars="${repo.stargazers_count || 0}">
            <span class="repo-category">${categoryLabels[category]}</span>
            <div class="repo-header">
                <a href="https://github.com/${name}" target="_blank" class="repo-name">${name}</a>
                <span class="repo-lang">${lang}</span>
            </div>
            <p class="repo-desc">${desc}</p>
            <div class="repo-meta">
                <span class="stars">⭐ ${stars}</span>
                <span>🍴 ${forks}</span>
            </div>
        </div>`;
    }).join('');
}

// Filter repos
function filterRepos(category) {
    const searchTerm = document.getElementById('search').value.toLowerCase();
    
    filteredRepos = allRepos.filter(repo => {
        // Category filter
        if (category !== 'all' && getCategory(repo) !== category) return false;
        
        // Search filter
        if (searchTerm) {
            const name = repo.full_name.toLowerCase();
            const desc = (repo.description || '').toLowerCase();
            if (!name.includes(searchTerm) && !desc.includes(searchTerm)) return false;
        }
        
        return true;
    });
    
    applySort();
}

// Sort repos
function applySort() {
    const sortValue = document.getElementById('sort').value;
    
    switch(sortValue) {
        case 'stars-desc':
            filteredRepos.sort((a, b) => (b.stargazers_count || 0) - (a.stargazers_count || 0));
            break;
        case 'stars-asc':
            filteredRepos.sort((a, b) => (a.stargazers_count || 0) - (b.stargazers_count || 0));
            break;
        case 'name-asc':
            filteredRepos.sort((a, b) => a.full_name.localeCompare(b.full_name));
            break;
        case 'name-desc':
            filteredRepos.sort((a, b) => b.full_name.localeCompare(a.full_name));
            break;
    }
    
    renderRepos();
    updateStats();
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    fetchRepos();
    
    // Search
    document.getElementById('search').addEventListener('input', () => {
        const activeFilter = document.querySelector('.filter-btn.active');
        filterRepos(activeFilter ? activeFilter.dataset.filter : 'all');
        applySort();
    });
    
    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterRepos(btn.dataset.filter);
            applySort();
        });
    });
    
    // Sort
    document.getElementById('sort').addEventListener('change', applySort);
});
