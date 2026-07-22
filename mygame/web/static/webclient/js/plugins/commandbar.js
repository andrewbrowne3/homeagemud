/*
 * Commandbar plugin — preset buttons for common Evennia commands.
 *
 * Each button entry has ONE of:
 *   - send:    'command text'    (sends immediately)
 *   - prefill: 'prefix '         (fills the input, waits for user to finish)
 *   - action:  'openCreateScene' (calls the named scenes_plugin method)
 *
 * Optional: group (info|scene|rp|acct), style (primary|danger|secondary).
 */
let commandbar_plugin = (function () {

    var COMMANDS = [
        // --- Info ---
        { label: 'Look',        send: 'look',          group: 'info' },
        { label: 'Who',         send: 'who',           group: 'info' },
        { label: 'Help',        send: 'help',          group: 'info' },

        // --- Scenes / channels ---
        { label: '+ Channel',   action: 'openCreateScene', group: 'scene', style: 'primary' },
        { label: 'Channels',    send: 'listscenes',    group: 'scene' },
        { label: 'Join...',     prefill: 'joinscene ', group: 'scene' },
        { label: 'Leave...',    prefill: 'leavescene ', group: 'scene' },

        // --- Land ---
        { label: 'Map',         action: 'openFiefMap', group: 'land', style: 'primary' },
        { label: 'Where',       send: 'where',         group: 'land' },
        { label: 'Build...',    prefill: 'build ',     group: 'land' },

        // --- RP actions ---
        { label: 'Say',         prefill: 'say ',       group: 'rp' },
        { label: 'Pose',        prefill: 'pose ',      group: 'rp' },
        { label: 'Whisper',     prefill: 'whisper ',   group: 'rp' },
        { label: 'Page',        prefill: 'page ',      group: 'rp' },

        // --- Account / character ---
        { label: 'My Chars',    send: 'charlist',      group: 'acct' },
        { label: 'New Char',    prefill: 'charcreate ', group: 'acct' },
        { label: 'Play As...',  prefill: 'ic ',        group: 'acct', style: 'primary' },
        { label: 'OOC',         send: 'ooc',           group: 'acct' },
        { label: 'Logout',      send: 'quit',          group: 'acct', style: 'danger' },
    ];

    var sendText = function (line) {
        if (window.Evennia && Evennia.isConnected && Evennia.isConnected()) {
            Evennia.msg('text', [line], {});
        }
    };

    var prefillInput = function (text) {
        var $input = $('.inputfield:last');
        if (!$input.length) $input = $('#inputfield');
        $input.focus().val(text);
        var el = $input[0];
        if (el && el.setSelectionRange) {
            el.setSelectionRange(text.length, text.length);
        }
    };

    // action name -> [plugin global, method]. Add an entry rather than another
    // if-branch when a plugin grows a button.
    var ACTIONS = {
        openCreateScene: ['scenes_plugin', 'openCreateDialog'],
        openFiefMap:     ['fiefmap_plugin', 'toggle'],
    };

    var runAction = function (name) {
        var target = ACTIONS[name];
        var plugin = target && window[target[0]];
        if (plugin && typeof plugin[target[1]] === 'function') {
            plugin[target[1]]();
            return;
        }
        console.warn('Unknown commandbar action:', name);
    };

    var btnClass = function (style) {
        switch (style) {
            case 'primary': return 'btn btn-sm btn-primary';
            case 'danger':  return 'btn btn-sm btn-outline-danger';
            default:        return 'btn btn-sm btn-outline-secondary';
        }
    };

    // Spoken names for the group boundaries, so a screen reader announces
    // "Land group" as you arrow into it rather than passing a silent divider.
    var GROUP_LABELS = {
        info:  'Information',
        scene: 'Channels',
        land:  'Land',
        rp:    'Roleplay',
        acct:  'Account',
    };

    // The bar is an ARIA toolbar: ONE tab stop, arrow keys move between buttons.
    // Nineteen buttons as nineteen tab stops is a long way to tab past to reach
    // the command line; a toolbar is a single stop you arrow across, which is the
    // pattern a screen-reader user already knows from every other toolbar.
    var barButtons = function () { return $('#commandbar .cmdbar-btn'); };

    var focusButton = function (index) {
        var $btns = barButtons();
        if (!$btns.length) return;
        var n = $btns.length;
        var i = ((index % n) + n) % n;   // wrap around either end
        $btns.attr('tabindex', -1);
        $btns.eq(i).attr('tabindex', 0).focus();
    };

    var onBarKeydown = function (ev) {
        var key = ev.key;
        if (key === 'Enter' || key === ' ' || key === 'Spacebar') {
            // Activate the button ourselves and stop the event, so default_in's
            // Enter handler does not also fire and send an empty command line.
            ev.preventDefault();
            ev.stopPropagation();
            if (document.activeElement) document.activeElement.click();
            return;
        }
        var $btns = barButtons();
        var here = $btns.index(document.activeElement);
        if (here < 0) here = 0;
        var next = null;
        if (key === 'ArrowRight' || key === 'ArrowDown') next = here + 1;
        else if (key === 'ArrowLeft' || key === 'ArrowUp') next = here - 1;
        else if (key === 'Home') next = 0;
        else if (key === 'End') next = $btns.length - 1;
        else return;                       // leave other keys alone
        // stopPropagation keeps default_in from yanking focus to the input as the
        // player arrows along the bar (the same grabber the fief map turns off).
        ev.preventDefault();
        ev.stopPropagation();
        focusButton(next);
    };

    var renderBar = function () {
        var $bar = $('#commandbar');
        if (!$bar.length) return;
        $bar.empty();

        // group consecutive commands so each group can be one labelled region
        var groups = [];
        COMMANDS.forEach(function (cmd) {
            var key = cmd.group || '_';
            if (!groups.length || groups[groups.length - 1].key !== key) {
                groups.push({ key: key, cmds: [] });
            }
            groups[groups.length - 1].cmds.push(cmd);
        });

        var globalIndex = 0;
        groups.forEach(function (grp, gi) {
            var $grp = $('<span role="group"></span>')
                .attr('aria-label', GROUP_LABELS[grp.key] || 'Commands')
                .css({
                    display: 'inline-block',
                    'border-left': gi ? '1px solid #555' : 'none',
                    'padding-left': gi ? '8px' : '0',
                    'margin-left': gi ? '2px' : '0',
                });
            grp.cmds.forEach(function (cmd) {
                var $btn = $('<button type="button" class="cmdbar-btn"></button>')
                    .attr('tabindex', globalIndex === 0 ? 0 : -1)
                    .addClass(btnClass(cmd.style))
                    .css({ 'margin-right': '4px', 'margin-bottom': '4px' })
                    .text(cmd.label);
                $btn.on('click', function () {
                    if (cmd.send) sendText(cmd.send);
                    else if (cmd.prefill) prefillInput(cmd.prefill);
                    else if (cmd.action) runAction(cmd.action);
                });
                $grp.append($btn);
                globalIndex++;
            });
            $bar.append($grp);
        });
    };

    var injectBar = function () {
        if ($('#commandbar').length) return;
        var $bar = $('<div id="commandbar"></div>')
            .attr('role', 'toolbar')
            .attr('aria-label', 'Game commands')
            .attr('aria-orientation', 'horizontal')
            .css({
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                'z-index': 500,
                background: '#1a1a1a',
                color: '#eee',
                padding: '4px 8px',
                'border-bottom': '1px solid #444',
                'line-height': '1.4',
                'font-size': '13px',
            });
        // one delegated handler drives roving focus for every button
        $bar.on('keydown', '.cmdbar-btn', onBarKeydown);
        $('body').append($bar);
        $('#clientwrapper').css('padding-top', '44px');
        $('body').css('padding-top', '0');
    };

    var init = function () {
        setTimeout(function () {
            injectBar();
            renderBar();
            console.log('Commandbar Plugin Initialized.');
        }, 500);
    };

    return {
        init: init,
        setCommands: function (list) { COMMANDS = list; renderBar(); },
    };
})();
window.plugin_handler.add('commandbar', commandbar_plugin);
