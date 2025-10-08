document.addEventListener('DOMContentLoaded', () => {

    // --- CONFIGURATION ---
    const ADMIN_PIN = "1234";
    const FEEDING_COOLDOWN_MINUTES = 240; // 4 hours
    const FEEDING_WARNING_MINUTES = 720; // 12 hours
    const SPRINKLER_AUTO_STOP_SECONDS = 30; // Auto-stop after 30 seconds

    // --- STATE MANAGEMENT ---
    const state = {
        pens: {
            lion: { isLocked: true, lastFed: null },
            tiger: { isLocked: true, lastFed: null },
            bear: { isLocked: true, lastFed: null },
            panda: { isLocked: true, lastFed: null },
        },
        zones: {
            savanna: { isActive: false, startTime: null, lastRun: null, runDuration: null, schedule: "07:00", scheduleEnabled: true, lastScheduleTrigger: null },
            jungle: { isActive: false, startTime: null, lastRun: null, runDuration: null, schedule: "21:30", scheduleEnabled: true, lastScheduleTrigger: null },
            tundra: { isActive: false, startTime: null, lastRun: null, runDuration: null, schedule: "11:22", scheduleEnabled: true, lastScheduleTrigger: null },
        }
    };

    // --- PIN MODAL LOGIC ---
    const pinModal = document.getElementById('pin-modal');
    const pinInput = document.getElementById('pin-input');
    const pinMessage = document.getElementById('pin-message');
    let onPinSuccess = null;

    const showPinModal = (message, successCallback) => {
        pinMessage.textContent = message;
        onPinSuccess = successCallback;
        pinInput.value = '';
        pinModal.classList.remove('hidden');
        pinInput.focus();
    };

    const hidePinModal = () => {
        pinModal.classList.add('hidden');
        onPinSuccess = null;
    };

    document.getElementById('pin-submit').addEventListener('click', () => {
        if (pinInput.value === ADMIN_PIN) {
            if (onPinSuccess) onPinSuccess();
            hidePinModal();
        } else {
            pinInput.style.border = '2px solid var(--red)';
            setTimeout(() => { pinInput.style.border = '1px solid var(--border-color)'; }, 1000);
        }
    });

    document.getElementById('pin-cancel').addEventListener('click', hidePinModal);

    // --- HELPER & CORE LOGIC FUNCTIONS ---
    const updateClock = () => {
        const now = new Date();
        const dateTimeString = now.toLocaleString(undefined, {
            dateStyle: 'full',
            timeStyle: 'medium'
        });
        document.getElementById('current-datetime').textContent = dateTimeString;
    };
    
    const checkSchedules = () => {
        const now = new Date();
        const currentTime = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
        
        for (const zone in state.zones) {
            const zoneState = state.zones[zone];

            if (zoneState.lastScheduleTrigger && zoneState.lastScheduleTrigger !== currentTime) {
                zoneState.lastScheduleTrigger = null;
            }

            if (zoneState.scheduleEnabled && !zoneState.isActive && zoneState.schedule === currentTime && zoneState.lastScheduleTrigger !== currentTime) {
                console.log(`Auto-starting sprinkler for ${zone} zone.`);
                zoneState.isActive = true;
                zoneState.startTime = new Date();
                zoneState.lastScheduleTrigger = currentTime;
                renderAll();
            }
        }
    };

    const checkSprinklerDurations = () => {
        const now = new Date();
        for (const zone in state.zones) {
            const zoneState = state.zones[zone];
            if (zoneState.isActive && zoneState.startTime) {
                const elapsedMilliseconds = now - zoneState.startTime;
                if (elapsedMilliseconds >= SPRINKLER_AUTO_STOP_SECONDS * 1000) {
                    console.log(`Auto-stopping sprinkler for ${zone} zone after ${SPRINKLER_AUTO_STOP_SECONDS} seconds.`);
                    zoneState.isActive = false;
                    zoneState.runDuration = now - zoneState.startTime;
                    zoneState.lastRun = now;
                    zoneState.startTime = null;
                    renderAll();
                }
            }
        }
    };

    const formatDuration = (ms) => {
        if (!ms) return '--';
        let seconds = Math.floor(ms / 1000);
        let minutes = Math.floor(seconds / 60);
        seconds = seconds % 60;
        if (minutes > 0) {
            return `${minutes}m ${seconds}s`;
        }
        return `${seconds}s`;
    };
    
    const populateTimeSelects = () => {
        const hourSelects = document.querySelectorAll('.hour-select');
        const minuteSelects = document.querySelectorAll('.minute-select');
        
        for (let i = 0; i < 24; i++) {
            const value = i.toString().padStart(2, '0');
            const option = new Option(value, value);
            hourSelects.forEach(sel => sel.add(option.cloneNode(true)));
        }
        
        for (let i = 0; i < 60; i++) {
            const value = i.toString().padStart(2, '0');
            const option = new Option(value, value);
            minuteSelects.forEach(sel => sel.add(option.cloneNode(true)));
        }
    };

    // --- RENDER FUNCTIONS ---
    const renderGateControls = () => {
        const penStates = Object.values(state.pens);
        for (const pen in state.pens) {
            const statusEl = document.getElementById(`${pen}-lock-status`);
            const buttonEl = document.querySelector(`#gate-controls [data-pen="${pen}"] button`);
            if (state.pens[pen].isLocked) {
                statusEl.textContent = 'LOCKED';
                statusEl.className = 'status locked';
                buttonEl.textContent = 'Unlock';
            } else {
                statusEl.textContent = 'UNLOCKED';
                statusEl.className = 'status unlocked';
                buttonEl.textContent = 'Lock';
            }
        }
        const lockAllButton = document.querySelector('[data-action="lockAll"]');
        const unlockAllButton = document.querySelector('[data-action="unlockAll"]');
        const areAllLocked = penStates.every(p => p.isLocked);
        const areAllUnlocked = penStates.every(p => !p.isLocked);
        lockAllButton.disabled = areAllLocked;
        unlockAllButton.disabled = areAllUnlocked;
    };

    const renderFeedingControls = () => {
        const now = new Date();
        for (const pen in state.pens) {
            const statusEl = document.getElementById(`${pen}-feed-status`);
            const buttonEl = document.querySelector(`#feeding-controls [data-pen="${pen}"] button`);
            
            if (!state.pens[pen].lastFed) {
                statusEl.innerHTML = `Last Fed: Never <span class="error">NEEDS FEEDING!</span>`;
                buttonEl.textContent = 'Feed Now';
                continue;
            }
            const minutesSinceFed = (now - state.pens[pen].lastFed) / 60000;
            const lastFedTime = state.pens[pen].lastFed.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit'});
            
            buttonEl.disabled = false;
            buttonEl.textContent = 'Feed Now';
            buttonEl.classList.remove('warning');

            if (minutesSinceFed < FEEDING_COOLDOWN_MINUTES) {
                statusEl.innerHTML = `Last Fed: ${lastFedTime} (Cooldown Active)`;
                buttonEl.textContent = 'Override & Feed';
                buttonEl.classList.add('warning');
            } else if (minutesSinceFed > FEEDING_WARNING_MINUTES) {
                statusEl.innerHTML = `Last Fed: ${lastFedTime} <span class="warning">FEEDING DUE!</span>`;
            } else {
                statusEl.innerHTML = `Last Fed: ${lastFedTime}`;
            }
        }
    };
    
    const renderSprinklerControls = () => {
        for (const zone in state.zones) {
            const statusEl = document.getElementById(`${zone}-sprinkler-status`);
            const lastRunEl = document.getElementById(`${zone}-sprinkler-last-run`);
            const durationEl = document.getElementById(`${zone}-sprinkler-duration`);
            const buttonEl = document.querySelector(`#sprinkler-controls [data-zone="${zone}"] button`);
            const scheduleCheckbox = document.getElementById(`${zone}-schedule-enable`);
            const hourSelect = document.querySelector(`.hour-select[data-zone="${zone}"]`);
            const minuteSelect = document.querySelector(`.minute-select[data-zone="${zone}"]`);
            
            if (state.zones[zone].isActive) {
                statusEl.textContent = 'ACTIVE';
                statusEl.className = 'status active';
                buttonEl.textContent = 'Deactivate';
            } else {
                statusEl.textContent = 'INACTIVE';
                statusEl.className = 'status inactive';
                buttonEl.textContent = 'Activate';
            }

            if (state.zones[zone].lastRun) {
                const lastRunTime = state.zones[zone].lastRun.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit'});
                lastRunEl.textContent = `Last Run: ${lastRunTime}`;
            } else {
                lastRunEl.textContent = 'Last Run: Never';
            }

            durationEl.textContent = `Duration: ${formatDuration(state.zones[zone].runDuration)}`;
            
            const zoneState = state.zones[zone];
            scheduleCheckbox.checked = zoneState.scheduleEnabled;
            hourSelect.disabled = !zoneState.scheduleEnabled;
            minuteSelect.disabled = !zoneState.scheduleEnabled;

            const [hour, minute] = zoneState.schedule.split(':');
            hourSelect.value = hour;
            minuteSelect.value = minute;
        }
    };

    const renderAll = () => {
        renderGateControls();
        renderFeedingControls();
        renderSprinklerControls();
    };

    // --- EVENT LISTENERS ---
    const dashboard = document.querySelector('.dashboard');

    dashboard.addEventListener('click', (e) => {
        if (!e.target.matches('.control-button')) return;
        const action = e.target.dataset.action;
        const pen = e.target.closest('.control-group')?.dataset.pen;
        const zone = e.target.closest('.control-group')?.dataset.zone;
        
        if (action === 'toggleLock' && pen) {
            const isUnlocking = state.pens[pen].isLocked;
            if (!isUnlocking) {
                state.pens[pen].isLocked = true;
            } else {
                const lockedPens = Object.values(state.pens).filter(p => p.isLocked).length;
                if (lockedPens === 1) {
                    showPinModal(`This will unlock the final pen. Please confirm.`, () => {
                        state.pens[pen].isLocked = false;
                        renderAll();
                    });
                } else {
                    state.pens[pen].isLocked = false;
                }
            }
        }
        if (action === 'lockAll') {
            Object.keys(state.pens).forEach(p => state.pens[p].isLocked = true);
        }
        if (action === 'unlockAll') {
            showPinModal('Unlock all pens simultaneously?', () => {
                Object.keys(state.pens).forEach(p => state.pens[p].isLocked = false);
                renderAll();
            });
        }
        if (action === 'feed' && pen) {
            const now = new Date();
            const lastFed = state.pens[pen].lastFed;
            const minutesSinceFed = lastFed ? (now - lastFed) / 60000 : Infinity;
            const performFeed = () => {
                state.pens[pen].lastFed = new Date();
                renderAll();
            };
            if (minutesSinceFed < FEEDING_COOLDOWN_MINUTES) {
                showPinModal(`Override ${FEEDING_COOLDOWN_MINUTES/60}hr feeding cooldown for ${pen}?`, performFeed);
            } else {
                performFeed();
            }
        }
        if (action === 'toggleSprinkler' && zone) {
            const zoneState = state.zones[zone];
            zoneState.isActive = !zoneState.isActive;
            if (zoneState.isActive) {
                zoneState.startTime = new Date();
            } else {
                if (zoneState.startTime) {
                    zoneState.runDuration = new Date() - zoneState.startTime;
                    zoneState.lastRun = new Date();
                    zoneState.startTime = null;
                }
            }
        }
        if (action === 'activateAllSprinklers') {
             showPinModal('Activate all sprinkler zones?', () => {
                Object.keys(state.zones).forEach(z => {
                    if (!state.zones[z].isActive) {
                       state.zones[z].isActive = true;
                       state.zones[z].startTime = new Date();
                    }
                });
                renderAll();
            });
        }
        renderAll();
    });

    dashboard.addEventListener('change', (e) => {
        const target = e.target;
        if (target.matches('.schedule-select')) {
            const zone = target.dataset.zone;
            const hourSelect = document.querySelector(`.hour-select[data-zone="${zone}"]`);
            const minuteSelect = document.querySelector(`.minute-select[data-zone="${zone}"]`);
            state.zones[zone].schedule = `${hourSelect.value}:${minuteSelect.value}`;
            console.log(`Schedule for ${zone} updated to: ${state.zones[zone].schedule}`);
        }

        if (target.matches('.schedule-enable-checkbox')) {
            const zone = target.dataset.zone;
            state.zones[zone].scheduleEnabled = target.checked;
            renderSprinklerControls();
        }
    });

    // --- INITIALIZATION ---
    populateTimeSelects();
    state.pens.tiger.lastFed = new Date(Date.now() - 13 * 60 * 60 * 1000);
    state.pens.bear.lastFed = new Date(Date.now() - 1 * 60 * 60 * 1000);
    
    renderAll();
    
    // Set background tasks
    setInterval(updateClock, 1000);
    setInterval(checkSchedules, 1000);
    setInterval(checkSprinklerDurations, 1000); 
    setInterval(renderFeedingControls, 5000); 
});