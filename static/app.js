(function(){
  'use strict';

  /* ── Utilities ── */
  const money = n => '₹' + Math.round(Number(n)||0).toLocaleString('en-IN');
  const $ = id => document.getElementById(id);
  const qs = sel => document.querySelector(sel);
  const qsa = sel => document.querySelectorAll(sel);

  /* ── Flash auto-dismiss ── */
  qsa('.flash').forEach(el => setTimeout(() => { el.style.opacity='0'; el.style.transform='translateY(-5px)'; }, 4500));

  /* ═══════════════════════════════════════════════
     PLACE MODAL SYSTEM
  ═══════════════════════════════════════════════ */
  const ART_BG = [
    'linear-gradient(140deg,#c5d9c8,#e8e2cd)',
    'linear-gradient(140deg,#e6c8ad,#f3e9d7)',
    'linear-gradient(140deg,#c2d7d9,#e8e9dc)',
    'linear-gradient(140deg,#d8d8e7,#eee4d8)',
    'linear-gradient(140deg,#d2dfc3,#f2e5c9)',
    'linear-gradient(140deg,#e6d1c5,#d6e3e4)'
  ];

  function openPlaceModal(place, artIndex) {
    const modal = $('place-modal');
    if (!modal) return;
    const idx = (artIndex || 0) % ART_BG.length;

    $('modal-art').style.background = ART_BG[idx];
    $('modal-category').textContent = place.category;
    $('modal-place-name').textContent = place.name;
    $('modal-meta').innerHTML = `<span>★ ${place.rating} <small>rating</small></span><span>⌖ ${place.distance_km} km away</span>`;
    $('modal-desc').textContent = place.description;

    const tagsEl = $('modal-tags');
    tagsEl.innerHTML = '';
    (place.tags || '').split(',').slice(0,5).forEach(t => {
      const s = document.createElement('span'); s.textContent = t.trim(); tagsEl.appendChild(s);
    });

    $('modal-hours').innerHTML = `🕐 ${place.best_time || place.hours || 'Check locally'}`;
    $('modal-budget-info').innerHTML = `💰 ${place.budget === 0 ? 'Free entry' : '₹' + place.budget + ' est./person'}`;
    const durationEl = $('modal-duration');
    if (durationEl) durationEl.innerHTML = `⏱ ${place.visit_duration ? place.visit_duration + ' hrs visit' : '~1–2 hrs'}`;
    const rushEl = $('modal-rush');
    if (rushEl) rushEl.innerHTML = `📊 ${place.rush_info || 'Weekday mornings quietest'}`;

    const reviewsList = $('modal-reviews-list');
    reviewsList.innerHTML = '';
    const reviews = place.reviews || [];
    if (reviews.length === 0) {
      reviewsList.innerHTML = '<p style="font-size:12px;color:var(--muted)">No reviews yet.</p>';
    } else {
      reviews.forEach(r => {
        const stars = '★'.repeat(r.rating) + '☆'.repeat(5 - r.rating);
        reviewsList.innerHTML += `<div class="review-card"><div class="review-header"><span class="review-user">${r.user}</span><span class="review-stars">${stars}</span></div><p class="review-text">${r.text}</p></div>`;
      });
    }

    const addBtn = $('modal-add-itinerary');
    const saveBtn = $('modal-save-place');
    const dirBtn = $('modal-directions');
    const webBtn = $('modal-website');

    addBtn.dataset.place = place.name;
    if (window.LOGGED_IN) {
      saveBtn.onclick = () => {
        const form = document.createElement('form');
        form.method = 'post';
        form.action = `/save-place/${encodeURIComponent(place.name)}`;
        document.body.appendChild(form);
        form.submit();
      };
    } else {
      saveBtn.onclick = () => { window.location.href = '/signup'; };
    }
    dirBtn.href = `https://www.google.com/maps/dir/?api=1&destination=${place.lat},${place.lng}`;
    webBtn.href = place.website || '#';

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }

  function closePlaceModal() {
    const modal = $('place-modal');
    if (modal) { modal.style.display = 'none'; document.body.style.overflow = ''; }
  }

  const placeModal = $('place-modal');
  if (placeModal) {
    placeModal.addEventListener('click', e => { if (e.target === placeModal) closePlaceModal(); });
    const closeBtn = $('modal-close-btn');
    if (closeBtn) closeBtn.addEventListener('click', closePlaceModal);
  }

  function bindPlaceCards(container) {
    (container || document).querySelectorAll('.place-card[data-place]').forEach((card, i) => {
      const placeData = card.dataset.place;
      if (!placeData) return;
      let place;
      try { place = JSON.parse(placeData); } catch(e) { return; }
      card.addEventListener('click', e => {
        if (e.target.closest('.place-actions')) return;
        openPlaceModal(place, i);
      });
      card.addEventListener('keydown', e => {
        if ((e.key === 'Enter' || e.key === ' ') && !e.target.closest('.place-actions')) {
          e.preventDefault();
          openPlaceModal(place, i);
        }
      });
    });
  }
  bindPlaceCards(document);

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { closePlaceModal(); closeItinModal(); }
  });

  /* ═══════════════════════════════════════════════
     ADD TO ITINERARY FLOW
  ═══════════════════════════════════════════════ */
  let pendingPlace = null;

  function openItinModal(placeName) {
    pendingPlace = placeName;
    const modal = $('itinerary-picker-modal');
    if (!modal) return;

    if (!window.LOGGED_IN) { window.location.href = '/signup'; return; }

    $('itin-place-name-label').textContent = placeName;
    $('itin-step-choose').style.display = 'block';
    $('itin-step-create').style.display = 'none';

    loadItineraries(placeName);
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }

  function closeItinModal() {
    const modal = $('itinerary-picker-modal');
    if (modal) { modal.style.display = 'none'; document.body.style.overflow = ''; }
    pendingPlace = null;
  }

  function loadItineraries(placeName) {
    const list = $('itin-list');
    if (!list) return;
    list.innerHTML = '<p style="font-size:12px;color:var(--muted);padding:10px 0">Loading your trips…</p>';
    fetch('/api/itineraries')
      .then(r => r.json())
      .then(data => {
        const trips = data.trips || [];
        if (trips.length === 0) {
          list.innerHTML = '<p style="font-size:12px;color:var(--muted);padding:8px 0">No trips yet. Create your first one below!</p>';
        } else {
          list.innerHTML = '<div class="itin-list">' + trips.map(t =>
            `<button class="itin-choice-btn" data-trip-id="${t.id}" data-trip-title="${t.title}">
              <div><strong>${t.title}</strong><small>${t.trip_date || 'No date set'} · ${t.group_size} ${t.group_size===1?'person':'people'}</small></div>
              <span class="itin-arrow">＋</span>
            </button>`
          ).join('') + '</div>';
          list.querySelectorAll('.itin-choice-btn').forEach(btn => {
            btn.addEventListener('click', () => addToExistingTrip(btn.dataset.tripId, btn.dataset.tripTitle, placeName));
          });
        }
      })
      .catch(() => { list.innerHTML = '<p style="font-size:12px;color:#c0392b">Could not load trips. Please try again.</p>'; });
  }

  function addToExistingTrip(tripId, tripTitle, placeName) {
    fetch(`/trip/${tripId}/add-stop`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ place_name: placeName })
    })
    .then(r => r.json())
    .then(data => {
      if (data.ok) { closeItinModal(); showToast(`"${placeName}" added to "${tripTitle}"! 🎉`); }
      else showToast('Something went wrong.', 'error');
    })
    .catch(() => showToast('Network error. Please try again.', 'error'));
  }

  function showToast(msg, type) {
    const toast = document.createElement('div');
    toast.className = `flash ${type === 'error' ? 'error' : 'success'}`;
    toast.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);z-index:500;min-width:280px;text-align:center;box-shadow:0 8px 24px rgba(0,0,0,.15)';
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 400); }, 3200);
  }

  const itinModal = $('itinerary-picker-modal');
  if (itinModal) {
    itinModal.addEventListener('click', e => { if (e.target === itinModal) closeItinModal(); });
    const ic = $('itin-modal-close'); if (ic) ic.addEventListener('click', closeItinModal);
  }

  const itinCreateNewBtn = $('itin-create-new-btn');
  if (itinCreateNewBtn) itinCreateNewBtn.addEventListener('click', () => {
    $('itin-step-choose').style.display = 'none';
    $('itin-step-create').style.display = 'block';
  });

  const itinBackBtn = $('itin-back-btn');
  if (itinBackBtn) itinBackBtn.addEventListener('click', () => {
    $('itin-step-create').style.display = 'none';
    $('itin-step-choose').style.display = 'block';
  });

  const itinCreateSaveBtn = $('itin-create-save-btn');
  if (itinCreateSaveBtn) itinCreateSaveBtn.addEventListener('click', () => {
    const name = $('new-trip-name').value.trim() || 'My trip';
    const date = $('new-trip-date').value;
    const people = $('new-trip-people').value || 2;
    const bud = $('new-trip-budget').value || 0;
    const startLoc = $('new-trip-start').value || '';
    const place = pendingPlace;
    const form = document.createElement('form');
    form.method = 'post'; form.action = '/planner';
    const fields = { title: name, trip_date: date, group_size: people, budget: bud, start_location: startLoc,
      'stop_name[]': place, 'stop_date[]': date, 'start_time[]': '', 'end_time[]': '',
      'transport[]': 'public', 'cost[]': '0', 'entry_cost[]': '0', 'stop_notes[]': '' };
    Object.entries(fields).forEach(([k, v]) => {
      const inp = document.createElement('input'); inp.type='hidden'; inp.name=k; inp.value=v; form.appendChild(inp);
    });
    document.body.appendChild(form); form.submit();
  });

  const modalAddBtn = $('modal-add-itinerary');
  if (modalAddBtn) modalAddBtn.addEventListener('click', () => {
    const place = modalAddBtn.dataset.place;
    closePlaceModal();
    openItinModal(place);
  });

  /* ── .add-stop buttons ── */
  function bindAddStopBtns(root) {
    (root || document).querySelectorAll('.add-stop').forEach(btn => {
      btn.addEventListener('click', e => {
        e.stopPropagation();
        const name = btn.dataset.place;
        if (!window.LOGGED_IN) { window.location.href = '/signup'; return; }
        openItinModal(name);
      });
    });
  }
  bindAddStopBtns(document);

  /* ═══════════════════════════════════════════════
     PLANNER PAGE  (only runs on planner page)
  ═══════════════════════════════════════════════ */
  if (window.PLANNER_ENABLED) {
    const container = $('stops-container');
    const addBtn = $('add-stop');
    const dateInput = $('trip-date');
    const budgetInput = $('group-budget');

    if (container) {
      if (dateInput) {
      dateInput.addEventListener('change', () => {
        qsa('.stop-date').forEach(d => { if (!d.value) d.value = dateInput.value; });
      });
    }

    function renumber() {
      container.querySelectorAll('.stop-editor').forEach((s, i) => {
        const idx = String(i+1).padStart(2,'0');
        s.querySelector('.stop-index').textContent = 'STOP ' + idx;
        s.querySelector('.remove-stop').disabled = container.querySelectorAll('.stop-editor').length === 1;
      });
      const sc = $('stop-count'); if (sc) sc.textContent = container.querySelectorAll('.stop-editor').length;
      updateTotals();
    }

    function updateTotals() {
      let transport = 0, entry = 0;
      container.querySelectorAll('.stop-cost').forEach(i => transport += Number(i.value)||0);
      container.querySelectorAll('.stop-entry-cost').forEach(i => entry += Number(i.value)||0);
      const total = transport + entry;
      const b = Number(budgetInput ? budgetInput.value : 0)||0;
      const remaining = b - total;

      const tc = $('total-cost'); if (tc) tc.textContent = money(total);
      const trc = $('transport-cost'); if (trc) trc.textContent = money(transport);
      const ec = $('entry-cost-total'); if (ec) ec.textContent = money(entry);
      const bl = $('budget-label'); if (bl) bl.textContent = money(b);
      const rem = $('remaining'); if (rem) { rem.textContent = money(remaining); rem.style.color = total > b ? '#b24a3c' : ''; }
      const mf = $('budget-meter-fill'); if (mf) mf.style.width = (b > 0 ? Math.min(100, total/b*100) : 0) + '%';
      const bw = $('budget-warning');
      if (bw) bw.textContent = total > b ? '⚠ Estimated spend exceeds your budget.' : 'Transport + entry cost estimates.';
      const gs = qs('[name=group_size]');
      const pl = $('people-label'); if (pl && gs) pl.textContent = (gs.value||1) + ' people';

      updateEstimatedTime();
    }

    function updateEstimatedTime() {
      // Calculate total duration based on filled stops
      const ALL = window.ALL_PLACES || [];
      let totalMins = 0;
      container.querySelectorAll('[name="stop_name[]"]').forEach(inp => {
        const pName = (inp.value || '').trim().toLowerCase();
        const found = ALL.find(p => p.name.toLowerCase() === pName);
        const dur = found ? (found.visit_duration || 1.5) : 1.5;
        totalMins += dur * 60;
        totalMins += 30; // avg travel between stops
      });
      const hrs = Math.floor(totalMins / 60);
      const mins = Math.round(totalMins % 60);
      const durEl = $('estimated-duration');
      if (durEl) durEl.textContent = hrs > 0 ? `~${hrs}h ${mins > 0 ? mins + 'm' : ''}` : `~${mins}m`;
    }

    function bindStop(s) {
      s.querySelector('.remove-stop').addEventListener('click', () => {
        if (container.querySelectorAll('.stop-editor').length > 1) { s.remove(); renumber(); }
      });
      s.querySelectorAll('input,select').forEach(i => i.addEventListener('input', updateTotals));
      // Auto-fill entry cost from place data
      const nameInp = s.querySelector('[name="stop_name[]"]');
      if (nameInp) nameInp.addEventListener('change', () => {
        const ALL = window.ALL_PLACES || [];
        const found = ALL.find(p => p.name.toLowerCase() === nameInp.value.trim().toLowerCase());
        if (found) {
          const entryInp = s.querySelector('.stop-entry-cost');
          if (entryInp && !entryInp.dataset.edited) entryInp.value = found.budget || 0;
          const notesInp = s.querySelector('[name="stop_notes[]"]');
          if (notesInp && !notesInp.value) {
            const hints = [];
            if (found.best_time) hints.push('Best: ' + found.best_time);
            if (found.rush_info) hints.push(found.rush_info);
            notesInp.value = hints.join(' · ');
          }
        }
        updateTotals();
      });
      // Mark entry cost as manually edited
      const entryInp = s.querySelector('.stop-entry-cost');
      if (entryInp) entryInp.addEventListener('input', () => { entryInp.dataset.edited = '1'; updateTotals(); });
    }

    if (addBtn) addBtn.addEventListener('click', () => {
      const old = container.querySelector('.stop-editor');
      const clone = old.cloneNode(true);
      clone.querySelectorAll('input').forEach(i => {
        if (i.name==='start_time[]') i.value='';
        else if (i.name==='end_time[]') i.value='';
        else if (i.name==='cost[]' || i.classList.contains('stop-cost')) i.value='0';
        else if (i.classList.contains('stop-entry-cost')) { i.value='0'; delete i.dataset.edited; }
        else i.value='';
      });
      clone.querySelectorAll('select').forEach(i => i.selectedIndex=0);
      container.appendChild(clone);
      bindStop(clone);
      renumber();
      clone.scrollIntoView({ behavior:'smooth', block:'nearest' });
    });

    container.querySelectorAll('.stop-editor').forEach(bindStop);
    if (budgetInput) budgetInput.addEventListener('input', updateTotals);
    const gsInput = qs('[name=group_size]');
    if (gsInput) gsInput.addEventListener('input', updateTotals);

    // Pre-fill from sessionStorage
    const pending = sessionStorage.getItem('roamlyAddPlace');
    if (pending) {
      const first = container.querySelector('[name="stop_name[]"]');
      if (first) { first.value = pending; first.dispatchEvent(new Event('change')); }
      sessionStorage.removeItem('roamlyAddPlace');
    }

    renumber();

    // Smart Recommend button
    const recommendBtn = $('recommend-order-btn');
    if (recommendBtn) recommendBtn.addEventListener('click', buildRecommendedPlan);

    function buildRecommendedPlan() {
      const ALL = window.ALL_PLACES || [];
      const stops = [...container.querySelectorAll('[name="stop_name[]"]')]
        .map(i => i.value.trim()).filter(Boolean);
      if (stops.length < 2) { showToast('Add at least 2 stops to get a recommended order.'); return; }

      const enriched = stops.map(name => {
        const p = ALL.find(x => x.name.toLowerCase() === name.toLowerCase());
        return p || { name, distance_km: 10, best_time: 'Anytime', visit_duration: 1.5, rush_info: '' };
      });

      // Sort: morning places first (based on best_time keyword), then by distance
      const timeOrder = p => {
        const t = (p.best_time || '').toLowerCase();
        if (t.includes('dawn') || t.includes('early morning') || t.includes('5am') || t.includes('6am')) return 0;
        if (t.includes('morning') || t.includes('7am') || t.includes('8am') || t.includes('9am')) return 1;
        if (t.includes('late morning') || t.includes('10am') || t.includes('11am')) return 2;
        if (t.includes('afternoon') || t.includes('midday') || t.includes('noon') || t.includes('12pm')) return 3;
        if (t.includes('anytime')) return 2;
        if (t.includes('evening') || t.includes('4pm') || t.includes('5pm') || t.includes('sunset') || t.includes('dusk')) return 5;
        if (t.includes('late evening') || t.includes('night') || t.includes('7pm')) return 6;
        return 3;
      };

      enriched.sort((a, b) => timeOrder(a) - timeOrder(b) || a.distance_km - b.distance_km);

      const panel = $('recommended-plan-panel');
      const list = $('recommended-plan-list');
      if (!panel || !list) return;

      let html = '';
      let cumMins = 0;
      const startHour = 9; // assume 9am start
      enriched.forEach((p, i) => {
        const startMin = startHour * 60 + cumMins;
        const h = Math.floor(startMin / 60) % 24;
        const m = startMin % 60;
        const timeStr = `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}`;
        const durMins = (p.visit_duration || 1.5) * 60;
        const endMin = startMin + durMins;
        const eh = Math.floor(endMin / 60) % 24;
        const em = endMin % 60;
        const endStr = `${String(eh).padStart(2,'0')}:${String(em).padStart(2,'0')}`;
        html += `
          <div class="rec-stop">
            <div class="rec-stop-num">${String(i+1).padStart(2,'0')}</div>
            <div class="rec-stop-body">
              <strong>${p.name}</strong>
              <span class="rec-time">🕐 ${timeStr} – ${endStr}</span>
              <span class="rec-tip rec-best-time">${p.best_time ? '✦ Best: ' + p.best_time : ''}</span>
              <span class="rec-rush">${p.rush_info ? '📊 ' + p.rush_info : ''}</span>
            </div>
          </div>`;
        cumMins += durMins + 35; // 35 min travel buffer between stops
      });

      list.innerHTML = html;
      panel.style.display = 'block';
      panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    const plannerForm = $('planner-form');
    if (plannerForm) plannerForm.addEventListener('submit', e => {
      const stops = [...container.querySelectorAll('.stop-editor')];
      for (const s of stops) {
        const start = s.querySelector('[name="start_time[]"]').value;
        const end = s.querySelector('[name="end_time[]"]').value;
        if (start && end && end <= start) {
          e.preventDefault();
          alert('For each stop, end time must be later than start time.');
          return;
        }
      }
    });
    } // end if (container)
  } // end PLANNER_ENABLED


  /* ═══════════════════════════════════════════════
     FINDER PAGE  (only runs on finder page)
  ═══════════════════════════════════════════════ */
  if (window.FINDER_ENABLED) {
    const TOTAL_STEPS = 6;
    let currentStep = 1;
    const answers = { group: null, people: 2, vibes: [], budget: null, distance: null, avoid: [], pace: null };

    function goToStep(n) {
      const old = qs('.finder-step.active');
      if (old) old.classList.remove('active');
      const target = $('step-' + n);
      if (target) { target.classList.add('active'); currentStep = n; }
      updateFinderNav();
      updateProgressDots();
    }

    function updateFinderNav() {
      const prev = $('finder-prev-btn');
      const next = $('finder-next-btn');
      if (prev) prev.style.display = currentStep > 1 ? 'inline-flex' : 'none';
      if (next) next.textContent = currentStep === TOTAL_STEPS ? 'Find My Places ✦' : 'Next →';
    }

    function updateProgressDots() {
      qsa('.progress-dot').forEach((dot, i) => {
        dot.classList.toggle('active', i + 1 <= currentStep);
      });
    }

    function bindSingleSelect(stepEl, answerKey) {
      if (!stepEl) return;
      stepEl.querySelectorAll('.finder-opt:not(.multi-sel)').forEach(btn => {
        btn.addEventListener('click', () => {
          stepEl.querySelectorAll('.finder-opt:not(.multi-sel)').forEach(b => b.classList.remove('selected'));
          btn.classList.add('selected');
          answers[answerKey] = btn.dataset.val;
        });
      });
    }

    function bindMultiSelect(stepEl, answerKey) {
      if (!stepEl) return;
      stepEl.querySelectorAll('.finder-opt.multi-sel').forEach(btn => {
        btn.addEventListener('click', () => {
          btn.classList.toggle('selected');
          const val = btn.dataset.val;
          if (btn.classList.contains('selected')) {
            if (!answers[answerKey].includes(val)) answers[answerKey].push(val);
          } else {
            answers[answerKey] = answers[answerKey].filter(v => v !== val);
          }
        });
      });
    }

    bindSingleSelect($('step-1'), 'group');
    bindMultiSelect($('step-2'), 'vibes');
    bindSingleSelect($('step-3'), 'budget');
    bindSingleSelect($('step-4'), 'distance');
    bindMultiSelect($('step-5'), 'avoid');
    bindSingleSelect($('step-6'), 'pace');

    const pcInput = $('people-count');
    if (pcInput) pcInput.addEventListener('input', () => { answers.people = parseInt(pcInput.value)||2; });

    const nextBtn = $('finder-next-btn');
    if (nextBtn) nextBtn.addEventListener('click', () => {
      if (currentStep < TOTAL_STEPS) goToStep(currentStep + 1);
      else showFinderResults();
    });

    const prevBtn = $('finder-prev-btn');
    if (prevBtn) prevBtn.addEventListener('click', () => { if (currentStep > 1) goToStep(currentStep - 1); });

    const restartBtn = $('finder-restart-btn');
    if (restartBtn) restartBtn.addEventListener('click', () => {
      const rw = $('finder-results-wrap'); if (rw) rw.style.display = 'none';
      const fw = $('finder-form-wrap'); if (fw) fw.style.display = 'block';
      qsa('.finder-opt').forEach(b => b.classList.remove('selected'));
      answers.group=null; answers.vibes=[]; answers.budget=null; answers.distance=null; answers.avoid=[]; answers.pace=null;
      goToStep(1);
    });

    function showFinderResults() {
      const places = window.ALL_PLACES || [];
      let results = places.filter(p => {
        if (answers.budget === 'free' && p.budget > 0) return false;
        if (answers.budget === 'low' && p.budget >= 300) return false;
        if (answers.budget === 'mid' && p.budget >= 700) return false;
        if (answers.distance && answers.distance !== '50') {
          if (p.distance_km > parseFloat(answers.distance)) return false;
        }
        if (answers.vibes.length > 0) {
          const haystack = (p.tags + ' ' + p.category + ' ' + p.description).toLowerCase();
          if (!answers.vibes.some(v => haystack.includes(v))) return false;
        }
        return true;
      });

      results.sort((a, b) => {
        const scoreA = answers.vibes.filter(v => (a.tags+a.description).toLowerCase().includes(v)).length;
        const scoreB = answers.vibes.filter(v => (b.tags+b.description).toLowerCase().includes(v)).length;
        if (scoreB !== scoreA) return scoreB - scoreA;
        return b.rating - a.rating;
      });

      const limit = answers.pace === 'chill' ? 3 : answers.pace === 'packed' ? 8 : 5;
      results = results.slice(0, limit);

      const grid = $('finder-results-grid');
      if (!grid) return;

      if (results.length === 0) {
        grid.innerHTML = `<div class="empty-state"><span>⌕</span><h3>No perfect match found.</h3><p>Try widening your budget or distance.</p><a class="btn btn-primary" href="/discover">Browse all places</a></div>`;
      } else {
        grid.innerHTML = results.map((p, i) => `
          <article class="place-card" data-place='${JSON.stringify(p).replace(/'/g,"&#39;")}' tabindex="0" role="button" aria-label="View ${p.name}">
            <div class="place-art art-${i % 6}">
              <span class="place-category">${p.category}</span>
              <span class="place-spark">✳</span>
              <div class="place-art-caption">${p.name}</div>
            </div>
            <div class="place-content">
              <div class="place-meta"><span>★ ${p.rating} <small>rating</small></span><span>⌖ ${p.distance_km} km</span></div>
              <h3>${p.name}</h3>
              <p>${p.description.slice(0,110)}${p.description.length>110?'…':''}</p>
              <div class="tag-row">${p.tags.split(',').slice(0,3).map(t=>`<span>${t.trim()}</span>`).join('')}</div>
              <div class="place-info-pills">
                <span class="info-pill">⏱ ${p.visit_duration||1.5}h visit</span>
                <span class="info-pill">🕐 ${p.best_time||'Anytime'}</span>
              </div>
              <div class="place-bottom">
                <div><strong>${p.budget===0?'Free':'₹'+p.budget+' est.'}</strong><small>Entry estimate</small></div>
                <div class="place-actions" onclick="event.stopPropagation()">
                  <button class="icon-link icon-link-labelled add-stop" data-place="${p.name}">
                    <span class="icon-sym">＋</span><span class="icon-label">Add to Plan</span>
                  </button>
                </div>
              </div>
            </div>
          </article>`).join('');

        bindPlaceCards(grid);
        bindAddStopBtns(grid);
      }

      // Build suggested order
      const orderEl = $('finder-suggested-order');
      if (orderEl && results.length > 1) {
        const sorted = [...results].sort((a,b) => {
          const tOrder = p => {
            const t = (p.best_time||'').toLowerCase();
            if (t.includes('dawn')||t.includes('early morning')||t.includes('5am')||t.includes('6am')) return 0;
            if (t.includes('morning')||t.includes('7am')||t.includes('8am')) return 1;
            if (t.includes('late morning')||t.includes('10am')||t.includes('11am')) return 2;
            if (t.includes('anytime')) return 2;
            if (t.includes('afternoon')) return 3;
            if (t.includes('sunset')||t.includes('evening')||t.includes('dusk')) return 5;
            return 2;
          };
          return tOrder(a) - tOrder(b) || a.distance_km - b.distance_km;
        });

        let html = '<div class="suggested-route">';
        let cumMins = 0;
        sorted.forEach((p, i) => {
          const startMin = 9*60 + cumMins;
          const h = Math.floor(startMin/60)%24, m = startMin%60;
          const timeStr = `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}`;
          const durMins = (p.visit_duration||1.5)*60;
          const endMin = startMin + durMins;
          const eh = Math.floor(endMin/60)%24, em = endMin%60;
          const endStr = `${String(eh).padStart(2,'0')}:${String(em).padStart(2,'0')}`;
          html += `<div class="route-stop"><span class="route-num">${String(i+1).padStart(2,'0')}</span><div class="route-stop-info"><strong>${p.name}</strong><div class="route-meta"><span>🕐 ${timeStr}–${endStr}</span><span>⏱ ~${p.visit_duration||1.5}h</span>${p.best_time?`<span>✦ ${p.best_time}</span>`:''}</div>${p.rush_info?`<div class="route-rush">📊 ${p.rush_info}</div>`:''}</div></div>`;
          if (i < sorted.length-1) html += `<div class="route-arrow">↓ ~30 min travel</div>`;
          cumMins += durMins + 35;
        });
        const totalH = Math.floor((9*60+cumMins-35)/60)%24;
        const totalMin = (9*60+cumMins-35)%60;
        html += `<div class="route-total">Day wraps up around ${String(totalH).padStart(2,'0')}:${String(totalMin).padStart(2,'0')}</div></div>`;
        orderEl.innerHTML = html;
        orderEl.style.display = 'block';
      }

      const subtitle = $('finder-results-subtitle');
      if (subtitle) {
        const gl = {solo:'solo explorer',couple:'couple',friends:'friends group',family:'family'}[answers.group] || 'your group';
        subtitle.textContent = `${results.length} place${results.length!==1?'s':''} picked for a ${gl} of ${answers.people}.`;
      }

      const fw = $('finder-form-wrap'); if (fw) fw.style.display = 'none';
      const rw = $('finder-results-wrap'); if (rw) rw.style.display = 'block';
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Initialize
    goToStep(1);
  } // end FINDER_ENABLED

})();
