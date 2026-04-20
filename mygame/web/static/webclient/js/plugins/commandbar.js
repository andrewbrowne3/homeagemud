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

    var runAction = function (name) {
        if (name === 'openCreateScene'
            && window.scenes_plugin
            && typeof window.scenes_plugin.openCreateDialog === 'function') {
            window.scenes_plugin.openCreateDialog();
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

    var renderBar = function () {
        var $bar = $('#commandbar');
        if (!$bar.length) return;
        $bar.empty();
        var lastGroup = null;
        COMMANDS.forEach(function (cmd) {
            if (cmd.group && lastGroup && cmd.group !== lastGroup) {
                $bar.append('<span style="display: inline-block; width: 1px; height: 20px; background: #555; margin: 0 6px; vertical-align: middle;"></span>');
            }
            lastGroup = cmd.group || lastGroup;
            var $btn = $('<button type="button" style="margin-right: 4px; margin-bottom: 4px;"></button>')
                .addClass(btnClass(cmd.style))
                .text(cmd.label);
            $btn.on('click', function () {
                if (cmd.send) sendText(cmd.send);
                else if (cmd.prefill) prefillInput(cmd.prefill);
                else if (cmd.action) runAction(cmd.action);
            });
            $bar.append($btn);
        });
    };

    var injectBar = function () {
        if ($('#commandbar').length) return;
        var $bar = $('<div id="commandbar"></div>').css({
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
