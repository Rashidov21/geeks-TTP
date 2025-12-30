// Shared utilities for typing practice pages (TP_utils)
window.TP_utils = (function(){
    function showToast(msg, type='info', timeout=3000){
        let el = document.getElementById('tp-toast');
        if(!el){
            el = document.createElement('div');
            el.id = 'tp-toast';
            el.style.position = 'fixed';
            el.style.right = '16px';
            el.style.top = '16px';
            el.style.zIndex = 99999;
            document.body.appendChild(el);
        }
        el.innerHTML = `<div style="background:${type==='error'? '#fee2e2':'#eef2ff'}; color:${type==='error'?'#b91c1c':'#0f172a'}; padding:8px 12px; border-radius:8px; box-shadow:0 6px 18px rgba(2,6,23,0.08);">${msg}</div>`;
        if(timeout>0){
            setTimeout(()=>{ if(el) el.innerHTML=''; }, timeout);
        }
    }

    function animateCounter(el, from, to, duration=800){
        if(!el) return;
        const start = performance.now();
        function step(now){
            const t = Math.min(1,(now-start)/duration);
            const val = from + (to-from)*t;
            el.textContent = Math.round(val);
            if(t<1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    }

    async function autoSave(url, payload, csrf){
        try{
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
                body: JSON.stringify(payload)
            });
            const json = await res.json().catch(()=>null);
            return { ok: res.ok, status: res.status, body: json };
        }catch(e){
            return { ok: false, error: e };
        }
    }

    function updateProgressBar(barEl, original, typed){
        if(!barEl) return;
        const total = (original||'').length || 1;
        const pct = Math.min(100, Math.round(((typed||'').length/total)*100));
        barEl.style.width = pct + '%';
    }

    // Per-character highlighting helper: returns HTML string with spans
    function renderPerChar(original, typed){
        original = original || '';
        typed = typed || '';
        const len = original.length;
        const parts = [];
        for(let i=0;i<len;i++){
            const ch = original[i] === ' ' ? '&nbsp;' : escapeHtml(original[i]);
            let cls = 'pending';
            if(i < typed.length){ cls = (typed[i] === original[i]) ? 'correct' : 'incorrect'; }
            parts.push(`<span class="tp-char ${cls}" data-index="${i}">${ch}</span>`);
        }
        return parts.join('');
    }

    function escapeHtml(s){
        return String(s).replace(/[&<>"']/g, function(m){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]; });
    }

    // Offline save queue (very small): store pending payloads in localStorage under 'tp_offline_queue'
    function enqueueOfflineSave(payload){
        try{
            const key = 'tp_offline_queue';
            const arr = JSON.parse(localStorage.getItem(key) || '[]');
            arr.push({payload, ts: Date.now()});
            localStorage.setItem(key, JSON.stringify(arr));
        }catch(e){ console.warn('enqueueOfflineSave failed', e); }
    }
    async function flushOfflineQueue(url, csrf){
        try{
            const key = 'tp_offline_queue';
            const arr = JSON.parse(localStorage.getItem(key) || '[]');
            if(!arr.length) return;
            const remaining = [];
            for(const item of arr){
                try{
                    const res = await autoSave(url, item.payload, csrf);
                    if(!res.ok) remaining.push(item);
                }catch(e){ remaining.push(item); }
            }
            localStorage.setItem(key, JSON.stringify(remaining));
        }catch(e){ console.warn('flushOfflineQueue failed', e); }
    }

    return { showToast, animateCounter, autoSave, updateProgressBar, enqueueOfflineSave, flushOfflineQueue, renderPerChar, escapeHtml };
})();
