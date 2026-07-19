/*
 * Fief map plugin — a 3x3 grid view of a fief's land.
 *
 * The map is a rendering of the same state the text commands describe, not a
 * separate system: every cell action sends the OOB command a player could have
 * typed (fiefstep / fiefgoto / fiefsurvey), and the server's reply drives both
 * the grid and the spoken announcement. Clicking and typing cannot drift apart.
 *
 * Two levels, both always 3x3, so the screen never gets busier as you go in:
 *   fief level — nine wards; arrows move focus, Enter zooms into a ward
 *   ward level — nine plots; arrows send fiefstep, so the SERVER's cursor is
 *                the single source of truth and ward boundaries are crossed
 *                (and announced) exactly as they are in text
 *
 * Accessibility is the point of the layout, not a retrofit:
 *   - a real ARIA grid with roving tabindex, so readers treat it as a grid
 *   - an aria-live region carrying the server's own announcement
 *   - keys are bound to the GRID, never to the document, so the command input
 *     is never robbed of arrow keys or focus (see the default_in keydown bug,
 *     commit 559d740) — Escape always hands focus back to the input
 *
 * Listens for OOB: fief_overview, fief_where, fief_survey, fief_moved,
 *                  fief_built, fief_demolished
 */
let fiefmap_plugin = (function () {

    // Cells are laid out in the server's reading order (payload.order):
    // NW N NE / W C E / SW S SE. Index 4 is the centre.
    var state = {
        payload: null,
        level: 'fief',   // 'fief' | 'ward'
        focus: 4,        // index into the 3x3 currently being shown
        open: false,
    };

    var send = function (cmd, kwargs) {
        if (window.Evennia && Evennia.isConnected && Evennia.isConnected()) {
            Evennia.msg(cmd, [], kwargs || {});
        }
    };

    var esc = function (text) {
        return $('<div>').text(text === undefined || text === null ? '' : text).html();
    };

    // -- announcements ------------------------------------------

    var announce = function (text) {
        // Re-setting identical text does not re-trigger a reader, so clear first.
        var $live = $('#fiefmap-live');
        if (!$live.length) return;
        $live.text('');
        window.setTimeout(function () { $live.text(text); }, 50);
    };

    var cellLabel = function (cell, index) {
        if (state.level === 'fief') {
            var built = cell.structures
                ? cell.structures + (cell.structures === 1 ? ' structure' : ' structures')
                : 'nothing built';
            return cell.name + ' ward, ward ' + cell.number + ' of 9, '
                + built + ', ' + cell.acres_used + ' of ' + cell.acres_total
                + ' acres used.';
        }
        var names = (cell.structures || []).map(function (s) { return s.name; });
        var contents = names.length ? names.join(', ') : 'empty';
        var here = (state.payload && cell.address === state.payload.cursor)
            ? 'You are here. ' : '';
        return here + cell.spoken + ', ' + contents + ', '
            + cell.acres_used + ' of ' + cell.acres_total + ' acres used.';
    };

    // -- rendering ----------------------------------------------

    var cells = function () {
        if (!state.payload) return [];
        return state.level === 'fief' ? state.payload.wards : state.payload.plots;
    };

    var cellTitle = function (cell) {
        return state.level === 'fief' ? cell.name : cell.address.split('.')[1];
    };

    var cellDetail = function (cell) {
        if (state.level === 'fief') {
            return cell.acres_used + '/' + cell.acres_total;
        }
        var names = (cell.structures || []).map(function (s) { return s.name; });
        return (names.length ? names.join(', ') : '—') + '<br>'
            + cell.acres_used + '/' + cell.acres_total;
    };

    var render = function () {
        var $grid = $('#fiefmap-grid');
        if (!$grid.length || !state.payload) return;
        var list = cells();

        // Whether the grid owns the keyboard has to be sampled BEFORE the
        // rebuild below: emptying the grid destroys the focused cell, and the
        // browser drops focus to <body> the moment it goes. Sampling afterwards
        // always reports "not focused" and would strand the player.
        var active = document.activeElement;
        var hadFocus = !!active && ($grid[0] === active || $.contains($grid[0], active));

        var crumb = state.level === 'fief'
            ? esc(state.payload.fief)
            : esc(state.payload.fief) + ' ▸ ' + esc(state.payload.ward.name) + ' ward';
        $('#fiefmap-crumb').html(crumb);
        $('#fiefmap-back').toggle(state.level === 'ward');
        $grid.attr('aria-label', state.level === 'fief'
            ? 'Wards of ' + state.payload.fief
            : 'Plots of ' + state.payload.ward.name + ' ward');

        $grid.empty();
        list.forEach(function (cell, index) {
            var focused = index === state.focus;
            var isCursor = state.level === 'ward'
                && state.payload && cell.address === state.payload.cursor;
            var $cell = $('<div role="gridcell"></div>')
                .attr('tabindex', focused ? 0 : -1)
                .attr('aria-label', cellLabel(cell, index))
                .attr('data-index', index)
                .css({
                    border: isCursor ? '2px solid #7ab7ff' : '1px solid #555',
                    background: focused ? '#2c3a49' : '#1f1f1f',
                    'border-radius': '4px',
                    padding: '6px',
                    'aspect-ratio': '1',
                    display: 'flex',
                    'flex-direction': 'column',
                    'justify-content': 'center',
                    'align-items': 'center',
                    'text-align': 'center',
                    cursor: 'pointer',
                    overflow: 'hidden',
                    'font-size': '11px',
                    'line-height': '1.3',
                });
            $cell.html(
                '<strong style="font-size:12px;">' + esc(cellTitle(cell)) + '</strong>'
                + '<span style="color:#aaa;">' + cellDetail(cell) + '</span>'
            );
            $grid.append($cell);
        });

        // Only take the keyboard back if we already had it. render() runs on
        // every server payload, including answers to `where` and `survey` typed
        // at the command line -- reclaiming focus unconditionally rips the caret
        // out of the input mid-word, and from then on the player's arrow keys go
        // to whichever of the two they were not expecting.
        var $focused = $grid.children('[data-index="' + state.focus + '"]');
        if (state.open && hadFocus && $focused.length) $focused.focus();
    };

    // -- actions ------------------------------------------------

    var activate = function (index) {
        var list = cells();
        if (!list.length) return;
        var cell = list[index];
        if (!cell) return;
        if (state.level === 'fief') {
            // zoom in: the server moves its cursor to that ward's centre
            send('fiefgoto', { address: cell.ward });
            state.level = 'ward';
        } else {
            send('fiefsurvey', { address: cell.address });
        }
    };

    var zoomOut = function () {
        if (state.level === 'ward') {
            state.level = 'fief';
            // land the focus on the ward we just came out of
            var order = (state.payload && state.payload.order) || [];
            var ward = state.payload ? state.payload.ward.ward : null;
            var index = order.indexOf(ward);
            state.focus = index >= 0 ? index : 4;
            render();
            announce('Zoomed out to the whole fief. '
                + cellLabel(cells()[state.focus], state.focus));
            return true;
        }
        return false;
    };

    var moveFocus = function (dx, dy) {
        var row = Math.floor(state.focus / 3), col = state.focus % 3;
        var nrow = row + dy, ncol = col + dx;
        if (nrow < 0 || nrow > 2 || ncol < 0 || ncol > 2) {
            announce('That is the edge of the fief.');
            return;
        }
        state.focus = nrow * 3 + ncol;
        render();
        announce(cellLabel(cells()[state.focus], state.focus));
    };

    var DIRECTIONS = {
        ArrowUp: 'north', ArrowDown: 'south',
        ArrowLeft: 'west', ArrowRight: 'east',
    };

    var onKeydown = function (ev) {
        var key = ev.key;
        if (key === 'Escape') {
            ev.preventDefault();
            if (!zoomOut()) close();
            return;
        }
        if (key === 'Enter' || key === ' ' || key === 'Spacebar') {
            ev.preventDefault();
            activate(state.focus);
            return;
        }
        if (!DIRECTIONS[key]) return;   // let every other key through untouched
        ev.preventDefault();
        if (state.level === 'ward') {
            // the server owns the cursor at plot level; it will answer with
            // fief_moved, including any ward crossing or edge cue
            send('fiefstep', { direction: DIRECTIONS[key] });
        } else {
            var d = DIRECTIONS[key];
            moveFocus(d === 'east' ? 1 : d === 'west' ? -1 : 0,
                      d === 'south' ? 1 : d === 'north' ? -1 : 0);
        }
    };

    // -- server replies -----------------------------------------

    var syncFocusToCursor = function () {
        if (!state.payload || state.level !== 'ward') return;
        var order = state.payload.order || [];
        var plot = (state.payload.cursor || '').split('.')[1];
        var index = order.indexOf(plot);
        if (index >= 0) state.focus = index;
    };

    var onPayload = function (announceIt) {
        return function (args, kwargs) {
            if (!kwargs || !kwargs.cursor) return;
            state.payload = kwargs;
            syncFocusToCursor();
            render();
            if (announceIt && state.open) {
                var list = cells();
                if (list[state.focus]) {
                    announce(cellLabel(list[state.focus], state.focus));
                }
            }
        };
    };

    // -- panel --------------------------------------------------

    var open = function () {
        state.open = true;
        $('#fiefmap-panel').show();
        send('fief', {});            // ask for a fresh payload
        window.setTimeout(function () {
            var $cell = $('#fiefmap-grid').children('[data-index="' + state.focus + '"]');
            if ($cell.length) $cell.focus();
        }, 300);
    };

    var close = function () {
        state.open = false;
        $('#fiefmap-panel').hide();
        // hand focus back to the command line, never leave it floating
        var $input = $('.inputfield:last');
        if (!$input.length) $input = $('#inputfield');
        $input.focus();
    };

    var toggle = function () { state.open ? close() : open(); };

    var injectPanel = function () {
        if ($('#fiefmap-panel').length) return;
        var $panel = $('<div id="fiefmap-panel" role="dialog" aria-modal="false" '
                     + 'aria-label="Fief map"></div>');
        $panel.css({
            position: 'fixed',
            top: '60px',
            left: '50%',
            transform: 'translateX(-50%)',
            width: 'min(92vw, 380px)',
            'z-index': 900,
            background: '#161616',
            color: '#eee',
            border: '1px solid #555',
            'border-radius': '6px',
            padding: '10px',
            'box-shadow': '0 4px 18px rgba(0,0,0,0.6)',
            display: 'none',
            'font-size': '13px',
        });
        $panel.html([
            '<div style="display:flex; align-items:center; gap:6px; margin-bottom:8px;">',
            '  <button id="fiefmap-back" class="btn btn-sm btn-outline-secondary" ',
            '          type="button" aria-label="Back to the whole fief">↑</button>',
            '  <strong id="fiefmap-crumb" style="flex:1;"></strong>',
            '  <button id="fiefmap-close" class="btn btn-sm btn-outline-secondary" ',
            '          type="button" aria-label="Close the map">✕</button>',
            '</div>',
            '<div id="fiefmap-grid" role="grid" ',
            '     style="display:grid; grid-template-columns:repeat(3,1fr); gap:6px;"></div>',
            '<p style="color:#888; font-size:11px; margin:8px 0 0;">',
            '  Arrow keys move, Enter opens, Escape goes back.</p>',
            '<div id="fiefmap-live" aria-live="polite" role="status" ',
            '     style="position:absolute; width:1px; height:1px; overflow:hidden; ',
            '            clip:rect(0 0 0 0); white-space:nowrap;"></div>',
        ].join('\n'));
        $('body').append($panel);

        // bound to the grid, NOT the document: the input keeps its arrow keys
        $('#fiefmap-grid').on('keydown', onKeydown);
        $('#fiefmap-grid').on('click', '[data-index]', function () {
            state.focus = parseInt($(this).attr('data-index'), 10);
            render();
            activate(state.focus);
        });
        $('#fiefmap-close').on('click', close);
        $('#fiefmap-back').on('click', function () {
            if (!zoomOut()) close();
        });
    };

    var init = function () {
        setTimeout(function () {
            injectPanel();
            if (window.Evennia && Evennia.emitter) {
                // fief_moved is the only one that should speak on arrival: the
                // others are answers to an explicit request, already narrated
                // in the message window.
                Evennia.emitter.on('fief_overview', onPayload(false));
                Evennia.emitter.on('fief_where', onPayload(false));
                Evennia.emitter.on('fief_survey', onPayload(false));
                Evennia.emitter.on('fief_moved', onPayload(true));
                Evennia.emitter.on('fief_built', onPayload(true));
                Evennia.emitter.on('fief_demolished', onPayload(true));
            }
            console.log('Fiefmap Plugin Initialized.');
        }, 500);
    };

    return {
        init: init,
        open: open,
        close: close,
        toggle: toggle,
    };
})();
window.fiefmap_plugin = fiefmap_plugin;
window.plugin_handler.add('fiefmap', fiefmap_plugin);
