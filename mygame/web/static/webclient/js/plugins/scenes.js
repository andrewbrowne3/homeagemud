/*
 * Scenes plugin — Create Scene popup + active scene list.
 *
 * Sends OOB commands: createscene, joinscene, leavescene, listscenes.
 * Listens for OOB replies: scene_created, scene_joined, scene_left, scene_list.
 */
let scenes_plugin = (function () {

    var refreshTimer = null;

    var renderSceneList = function (scenes) {
        var $list = $("#scene-list").empty();
        var $empty = $("#scene-empty");
        if (!scenes || !scenes.length) {
            $empty.show();
            return;
        }
        $empty.hide();
        scenes.forEach(function (s) {
            var li = $('<li style="margin-bottom: 6px; padding: 4px; border: 1px solid #555; border-radius: 4px; cursor: pointer;"></li>');
            li.html(
                '<strong>' + $('<div>').text(s.title).html() + '</strong>' +
                ' <span style="color:#888; font-size:0.9em;">(' + s.member_count + ')</span>' +
                (s.description ? '<div style="font-size: 0.85em; color: #aaa;">' + $('<div>').text(s.description).html() + '</div>' : '')
            );
            li.attr('data-scene-id', s.id);
            li.attr('data-scene-title', s.title);
            li.on('click', function () {
                Evennia.msg('joinscene', [], { scene_id: s.id });
            });
            $list.append(li);
        });
    };

    var openCreateDialog = function () {
        $('#create-scene-dialog').remove();
        var html = [
            '<form id="create-scene-form" onsubmit="return false;">',
            '  <div style="margin-bottom: 8px;"><label>Title<br/>',
            '    <input type="text" id="scene-title-input" class="form-control" required maxlength="80" style="width: 100%;" /></label></div>',
            '  <div style="margin-bottom: 8px;"><label>Description (optional)<br/>',
            '    <textarea id="scene-desc-input" class="form-control" rows="3" style="width: 100%;"></textarea></label></div>',
            '  <div style="text-align: right;">',
            '    <button type="button" id="scene-create-cancel" class="btn btn-sm btn-secondary">Cancel</button>',
            '    <button type="submit" id="scene-create-submit" class="btn btn-sm btn-primary">Create</button>',
            '  </div>',
            '</form>'
        ].join('\n');
        popups_plugin.createDialog('create-scene-dialog', 'Create Scene', html);
        popups_plugin.openPopup('#create-scene-dialog');
        var dialog = $('#create-scene-dialog');
        dialog.css({ position: 'fixed', top: '20%', left: '30%', width: '360px', zIndex: 1000, background: '#222', color: '#eee', padding: '12px', border: '1px solid #555' });
        dialog.find('#scene-title-input').focus();
        dialog.find('#scene-create-cancel').on('click', function () {
            popups_plugin.closePopup('#create-scene-dialog');
        });
        dialog.find('#create-scene-form').on('submit', function () {
            var title = dialog.find('#scene-title-input').val().trim();
            var desc = dialog.find('#scene-desc-input').val().trim();
            if (!title) return false;
            Evennia.msg('createscene', [], { title: title, description: desc });
            popups_plugin.closePopup('#create-scene-dialog');
            return false;
        });
    };

    var refreshScenes = function () {
        if (Evennia && Evennia.isConnected && Evennia.isConnected()) {
            Evennia.msg('listscenes', [], {});
        }
    };

    var onSceneList = function (args, kwargs) {
        renderSceneList(kwargs.scenes || []);
    };
    var onSceneCreated = function (args, kwargs) { refreshScenes(); };
    var onSceneJoined = function (args, kwargs) { refreshScenes(); };
    var onSceneLeft = function (args, kwargs) { refreshScenes(); };

    var injectPanel = function () {
        if ($('#scene-panel').length) return;
        var $panel = $('<div id="scene-panel"></div>').css({
            position: 'fixed',
            top: '44px',
            right: 0,
            bottom: 0,
            width: '220px',
            'z-index': 500,
            background: '#1a1a1a',
            color: '#eee',
            padding: '8px',
            'border-left': '1px solid #444',
            'overflow-y': 'auto',
            'font-size': '13px',
        });
        $panel.html([
            '<div style="display: flex; gap: 4px; margin-bottom: 8px;">',
            '  <button id="create-scene-btn" class="btn btn-sm btn-primary" type="button" style="flex: 1;">+ Scene</button>',
            '  <button id="refresh-scenes-btn" class="btn btn-sm btn-outline-secondary" type="button">↻</button>',
            '</div>',
            '<h5 style="margin: 4px 0;">Active Scenes</h5>',
            '<ul id="scene-list" style="list-style: none; padding: 0; margin: 0;"></ul>',
            '<p id="scene-empty" style="color: #888; font-size: 0.9em; display: none;">No active scenes yet.</p>',
        ].join('\n'));
        $('body').append($panel);
        $('#clientwrapper').css('margin-right', '220px');
    };

    var init = function () {
        setTimeout(function () {
            injectPanel();
            $('#create-scene-btn').on('click', openCreateDialog);
            $('#refresh-scenes-btn').on('click', refreshScenes);

            if (Evennia && Evennia.emitter) {
                Evennia.emitter.on('scene_list', onSceneList);
                Evennia.emitter.on('scene_created', onSceneCreated);
                Evennia.emitter.on('scene_joined', onSceneJoined);
                Evennia.emitter.on('scene_left', onSceneLeft);
            }

            setTimeout(refreshScenes, 1500);
            refreshTimer = setInterval(refreshScenes, 30000);

            console.log('Scenes Plugin Initialized.');
        }, 500);
    };

    return {
        init: init,
        refreshScenes: refreshScenes,
        openCreateDialog: openCreateDialog,
    };
})();
window.scenes_plugin = scenes_plugin;
window.plugin_handler.add('scenes', scenes_plugin);
