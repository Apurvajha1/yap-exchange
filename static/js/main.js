window.currentTab = 'hot';
let chatInterval;
let lastMessageId = null;

document.addEventListener('DOMContentLoaded', () => {
    setupListeners();
    checkAuthStatus();
});

function safeClick(id, func) {
    const el = document.getElementById(id);
    if (el) el.onclick = func;
}

function setupListeners() {
    safeClick('show-signup', () => {
        document.getElementById('login-form').classList.add('hidden');
        document.getElementById('signup-form').classList.remove('hidden');
    });
    safeClick('show-login', () => {
        document.getElementById('signup-form').classList.add('hidden');
        document.getElementById('login-form').classList.remove('hidden');
    });
    safeClick('btn-account', () => {
        document.getElementById('account-modal').classList.remove('hidden');
    });

    safeClick('tab-hot', () => { window.currentTab = 'hot'; loadBoard(); });
    safeClick('tab-all', () => { window.currentTab = 'all'; loadBoard(); });

    safeClick('btn-login', login);
    safeClick('btn-signup', signup);
    safeClick('btn-logout-modal', logout);
    safeClick('add-target-btn', addTarget);
    safeClick('send-chat-btn', sendChat);

    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.onkeypress = (e) => { if(e.key === 'Enter') sendChat(); };
    }
}

async function checkAuthStatus() {
    try {
        const res = await fetch('/api/auth/status');
        if (!res.ok) return;

        const data = await res.json();
        if (data.logged_in) {
            document.getElementById('acc-username-display').textContent = data.username;
            document.getElementById('acc-balance-display').textContent = data.balance.toFixed(0) + " 💊";
            document.getElementById('header-username').textContent = data.username;

            if (data.is_boss && document.getElementById('btn-boss-panel')) {
                document.getElementById('btn-boss-panel').classList.remove('hidden');
            }

            const oldBalance = parseFloat(document.getElementById('user-balance').textContent || 0);
            const newBalance = parseFloat(data.balance);

            if (newBalance > oldBalance && oldBalance !== 0 && !data.is_boss) {
                alert("💊 DAILY STIMULUS: You received 1,000 Copium for surviving another day!");
            }

            document.getElementById('user-balance').textContent = newBalance.toFixed(0);
            document.getElementById('auth-container').classList.add('hidden');
            document.getElementById('main-app').classList.remove('hidden');

            loadBoard();
            loadLeaderboard();
            loadHotTargets();

            loadChat();
            chatInterval = setInterval(loadChat, 2000);
        }
    } catch (e) { console.error("Auth status check failed.", e); }
}

async function loadChat() {
    try {
        const res = await fetch('/api/chat');
        if (!res.ok) return;
        const messages = await res.json();
        const box = document.getElementById('chat-box');

        if (messages.length === 0) {
            if (lastMessageId !== null) {
                box.innerHTML = '<div class="empty-state">No one is yapping.</div>';
                lastMessageId = null;
            }
            return;
        }

        const newestId = messages[messages.length - 1].id;
        if (newestId !== lastMessageId) {
            box.innerHTML = messages.map(m => {
                const badge = m.is_admin ? `<span style="background: var(--danger-red); color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.6rem; margin-left: 5px; vertical-align: middle;">BOSS</span>` : '';
                const color = m.is_admin ? 'var(--danger-red)' : 'var(--neon-cyan)';
                return `
                    <div style="background: rgba(0,0,0,0.3); padding: 10px; border-radius: 6px; border-left: 2px solid ${color}; font-size: 0.9rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                            <span style="font-weight: bold; color: ${color};">${m.username} ${badge}</span>
                            <span style="color: var(--text-muted); font-size: 0.7rem;">
                                ${new Date(m.timestamp * 1000).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                            </span>
                        </div>
                        <div style="color: var(--text-main); word-wrap: break-word;">${m.text}</div>
                    </div>
                `;
            }).join('');
            box.scrollTop = box.scrollHeight;
            lastMessageId = newestId;
        }
    } catch (e) {}
}

async function sendChat() {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text) return;

    input.value = '';
    await fetch('/api/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({text}) });
    loadChat();
}

async function login() {
    try {
        const username = document.getElementById('login-user').value.trim();
        const password = document.getElementById('login-pass').value;
        const res = await fetch('/api/auth/login', {
            method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({username, password})
        });

        if (res.ok) { checkAuthStatus(); } else {
            const data = await res.json().catch(() => ({message: "SERVER CRASH: Check Python Error Logs!"}));
            alert(data.message || "Skill Issue: Wrong credentials.");
        }
    } catch (e) { alert("CRITICAL ERROR: Could not connect to Python server."); }
}

async function signup() {
    try {
        const username = document.getElementById('signup-user').value.trim();
        const password = document.getElementById('signup-pass').value;
        const res = await fetch('/api/auth/register', {
            method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({username, password})
        });

        const data = await res.json().catch(() => ({success: false, message: "SERVER CRASH: Check Python Error Logs!"}));
        if (data.success) {
            alert("Spawn successful! Now Login.");
            document.getElementById('show-login').click();
        } else { alert(data.message); }
    } catch (e) { alert("CRITICAL ERROR: Could not connect to Python server."); }
}

async function logout() {
    await fetch('/api/auth/logout', {method: 'POST'});
    location.reload();
}

async function addTarget() {
    const name = document.getElementById('new-target-name').value.trim();
    if (!name) return alert("You gotta name the target!");

    try {
        // Only sending the name to the server now
        const res = await fetch('/api/targets', {
            method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name: name})
        });
        const data = await res.json();

        if (data.success) {
            document.getElementById('new-target-name').value = '';
            loadBoard();
        } else { alert(data.message); }
    } catch (e) { alert("CRITICAL ERROR: Could not talk to the server."); }
}

async function loadBoard() {
    const res = await fetch('/api/targets');
    if (!res.ok) return;
    let targets = await res.json();

    targets.sort((a, b) => b.total_wagered - a.total_wagered);

    const btnHot = document.getElementById('tab-hot');
    const btnAll = document.getElementById('tab-all');

    if (window.currentTab === 'hot') {
        targets = targets.slice(0, 4);
        if(btnHot) btnHot.className = 'neon-btn';
        if(btnAll) btnAll.className = 'outline-btn';
    } else {
        if(btnHot) btnHot.className = 'outline-btn';
        if(btnAll) btnAll.className = 'neon-btn';
    }

    const container = document.getElementById('targets-container');
    container.innerHTML = '';

    if (targets.length === 0) {
        container.innerHTML = '<div class="empty-state" style="grid-column: 1 / -1;">No targets on the board yet.</div>';
        return;
    }

    targets.forEach(t => {
        const card = document.createElement('div');
        card.className = 'target-card';
        let buttons = '';
        for (const [dur, mult] of Object.entries(t.odds)) {
            const safeName = t.name.replace(/'/g, "\\'");
            buttons += `<button class="odd-btn" onclick="selectBet('${safeName}', '${dur}', ${mult})"><span class="odd-label">${dur}</span><span class="odd-value">${mult}x</span></button>`;
        }

        card.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 1rem;">
                <div class="target-name" style="margin-bottom:0;">🤡 ${t.name}</div>
                <div style="font-size:0.7rem; color:var(--text-muted); background:rgba(0,0,0,0.5); padding:3px 6px; border-radius:4px; border: 1px solid var(--glass-border);">
                    POOL: <span style="color:var(--copium-gold); font-weight:bold;">${t.total_wagered.toFixed(0)} 💊</span>
                </div>
            </div>
            <div class="odds-container">${buttons}</div>
        `;
        container.appendChild(card);
    });
}

async function loadLeaderboard() {
    const res = await fetch('/api/leaderboard');
    if (!res.ok) return;
    const users = await res.json();
    const container = document.getElementById('leaderboard-container');

    if (users.length === 0) {
        container.innerHTML = '<div class="empty-state" style="padding:1rem 0;">No active whales.</div>';
        return;
    }

    container.innerHTML = users.map((u, i) => {
        let medal = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : '💀';
        return `<div style="display:flex; justify-content:space-between; margin-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:5px;"><span>${medal} ${u.username}</span><span style="color:#00f0ff">${u.balance.toFixed(0)} 💊</span></div>`;
    }).join('');
}

async function loadHotTargets() {
    const res = await fetch('/api/hot_targets');
    if (!res.ok) return;
    const targets = await res.json();
    const container = document.getElementById('hot-targets-container');

    if (targets.length === 0) {
        container.innerHTML = '<div class="empty-state" style="padding:1rem 0;">No active bounties.</div>';
        return;
    }

    container.innerHTML = targets.map(t => {
        return `<div style="display:flex; justify-content:space-between; margin-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:5px;"><span>🎯 ${t.name}</span><span style="color:#ff2a2a">${t.total_wagered.toFixed(0)} 💊</span></div>`;
    }).join('');
}

window.selectBet = function(name, dur, mult) {
    window.currentBet = {name, dur, mult};
    document.getElementById('empty-slip').style.display = 'none';
    document.getElementById('active-slip').classList.remove('hidden');
    document.getElementById('slip-target').textContent = name;
    document.getElementById('slip-duration').textContent = `${dur} @ ${mult}x`;

    const stakeInput = document.getElementById('stake-input');
    const payoutText = document.getElementById('potential-payout');

    payoutText.textContent = `${(stakeInput.value * mult).toFixed(0)} 💊`;

    stakeInput.oninput = function() { payoutText.textContent = `${(this.value * mult).toFixed(0)} 💊`; };

    document.getElementById('place-bet-btn').onclick = async () => {
        const res = await fetch('/api/bet', {
            method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({stake: stakeInput.value, target: window.currentBet})
        });
        const data = await res.json();
        if (data.success) {
            alert("Contract Confirmed. The market has shifted.");
            document.getElementById('user-balance').textContent = data.new_balance.toFixed(0);
            if (document.getElementById('acc-balance-display')) {
                document.getElementById('acc-balance-display').textContent = data.new_balance.toFixed(0) + " 💊";
            }
            document.getElementById('active-slip').classList.add('hidden');
            document.getElementById('empty-slip').style.display = 'block';

            loadLeaderboard();
            loadHotTargets();
            loadBoard();
        } else { alert(data.message); }
    };
}
