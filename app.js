// ===== RepoHunter App =====

const API_BASE = ''; // Relative to current page
let allRepos = [];
let filteredRepos = [];
let repoMeta = {};

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

// ---------- Utilities ----------
function esc(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// ---------- Share ----------
function shareTo(type, url, title) {
    const target = url || window.location.href;
    const text = title || document.title;
    const eu = encodeURIComponent(target);
    const et = encodeURIComponent(text);

    if (type === 'facebook') {
        window.open(
            'https://www.facebook.com/sharer/sharer.php?u=' + eu,
            'share', 'width=640,height=560,scrollbars=yes,resizable=yes'
        );
    } else if (type === 'line') {
        window.open(
            'https://social-plugins.line.me/lineit/share?url=' + eu + '&text=' + et,
            'share', 'width=640,height=560,scrollbars=yes,resizable=yes'
        );
    } else if (type === 'copy') {
        copyText(target);
    }
}

function copyText(t) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(t).then(
            () => toast('✅ คัดลอกลิงก์แล้ว'),
            () => fallbackCopy(t)
        );
    } else {
        fallbackCopy(t);
    }
}

function fallbackCopy(t) {
    const ta = document.createElement('textarea');
    ta.value = t;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.top = '-1000px';
    document.body.appendChild(ta);
    ta.select();
    let ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    toast(ok ? '✅ คัดลอกลิงก์แล้ว' : '❌ คัดลอกไม่สำเร็จ');
}

let toastTimer;
function toast(msg) {
    let el = document.getElementById('toast');
    if (!el) {
        el = document.createElement('div');
        el.id = 'toast';
        el.className = 'toast';
        document.body.appendChild(el);
    }
    el.textContent = msg;
    el.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove('show'), 1800);
}

// Fetch repos data
async function fetchRepos() {
    try {
        const response = await fetch('data/repos.json');
        if (!response.ok) throw new Error('Failed to fetch');
        const data = await response.json();
        allRepos = data.repos || [];
        repoMeta = data._meta || {};
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
    const meta = repoMeta || {};
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
        const desc = repo.description_th || repo.description || 'ไม่มีคำอธิบาย';
        const descEn = repo.description || '';
        const name = repo.full_name;
        const shareTitle = name + ' — ' + desc;
        
        return `
        <div class="repo-card" data-category="${category}" data-name="${name.toLowerCase()}" data-stars="${repo.stargazers_count || 0}">
            <span class="repo-category">${categoryLabels[category]}</span>
            <div class="repo-header">
                <a href="https://github.com/${name}" target="_blank" class="repo-name">${name}</a>
                <span class="repo-lang">${lang}</span>
            </div>
            <p class="repo-desc">${esc(desc)}</p>
            ${descEn ? `<p class="repo-desc-en">${esc(descEn)}</p>` : ''}
            <div class="repo-meta">
                <span class="stars">⭐ ${stars}</span>
                <span>🍴 ${forks}</span>
                <div class="repo-share">
                    <button class="mini-share mini-fb" data-share="facebook" data-url="${esc(repo.html_url)}" data-title="${esc(shareTitle)}" title="แชร์ไป Facebook" aria-label="แชร์ไป Facebook">
                        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M22 12a10 10 0 1 0-11.6 9.9v-7H7.9V12h2.5V9.8c0-2.5 1.5-3.9 3.7-3.9 1.1 0 2.2.2 2.2.2v2.4h-1.2c-1.2 0-1.6.8-1.6 1.6V12h2.7l-.4 2.9h-2.3v7A10 10 0 0 0 22 12z"/></svg>
                    </button>
                    <button class="mini-share mini-line" data-share="line" data-url="${esc(repo.html_url)}" data-title="${esc(shareTitle)}" title="แชร์ไป LINE" aria-label="แชร์ไป LINE">
                        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2C6.5 2 2 5.7 2 10.3c0 4.1 3.6 7.5 8.5 8.2.3.1.8.2.9.5.1.3.1.7 0 1l-.1.9c0 .3-.2 1 .9.5s5.8-3.4 7.7-5.8c1.4-1.5 2.1-3.1 2.1-5.3C22 5.7 17.5 2 12 2z"/></svg>
                    </button>
                    <button class="mini-share mini-copy" data-share="copy" data-url="${esc(repo.html_url)}" title="คัดลอกลิงก์" aria-label="คัดลอกลิงก์">
                        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9.5 13.5a3 3 0 0 0 4.2 0l3-3a3 3 0 0 0-4.2-4.2l-1 1M14.5 10.5a3 3 0 0 0-4.2 0l-3 3a3 3 0 0 0 4.2 4.2l1-1"/></svg>
                    </button>
                </div>
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
        
        // Search filter (ค้นได้ทั้งชื่อ, คำอธิบายไทย, คำอธิบายอังกฤษ, topics)
        if (searchTerm) {
            const hay = [
                repo.full_name || '',
                repo.description_th || '',
                repo.description || '',
                (repo.topics || []).join(' ')
            ].join(' ').toLowerCase();
            if (!hay.includes(searchTerm)) return false;
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

    // Share buttons (delegated — ใช้ได้ทั้งปุ่มใน hero และบนการ์ด repo)
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('[data-share]');
        if (!btn) return;
        e.preventDefault();
        shareTo(btn.dataset.share, btn.dataset.url, btn.dataset.title);
    });
});
