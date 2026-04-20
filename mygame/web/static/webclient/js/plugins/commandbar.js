/*
 * Commandbar plugin — preset buttons for common Evennia commands.
 *
 * Each button either sends a command immediately (`send: "who"`) or
 * prefills the input field so the user can finish typing (`prefill: "say "`).
 *
 * Edit COMMANDS below to change the set.
 */
let commandbar_plugin = (function () {

    var COMMANDS = [
        { label: 'Look',      send: 'look' },
        { label: 'Who',       send: 'who' },
        { label: 'Inventory', send: 'inventory' },
        { label: 'Help',      send: 'help' },
        { label: 'Scenes',    send: 'listscenes' },
        { label: 'Say...',    prefill: 'say ' },
        { label: 'Pose...',   prefill: 'pose ' },
        { label: 'Whisper...',prefill: 'whisper ' },
        { label: 'Home',      send: 'home' },
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

    var renderBar = function () {
        var $bar = $('#commandbar');
        if (!$bar.length) return;
        $bar.empty();
        COMMANDS.forEach(function (cmd) {
            var $btn = $('<button type="button" class="btn btn-sm btn-outline-secondary" style="margin-right: 4px; margin-bottom: 4px;"></button>')
                .text(cmd.label);
            $btn.on('click', function () {
                if (cmd.send) sendText(cmd.send);
                else if (cmd.prefill) prefillInput(cmd.prefill);
            });
            $bar.append($btn);
        });
    };

    var init = function () {
        renderBar();
        console.log('Commandbar Plugin Initialized.');
    };

    return {
        init: init,
        setCommands: function (list) { COMMANDS = list; renderBar(); },
    };
})();
window.plugin_handler.add('commandbar', commandbar_plugin);
