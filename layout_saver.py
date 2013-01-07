import sublime, sublime_plugin

# TODO: don't save a single state, maintain a stack per window ID
class SublimeLayoutManager:
    def __init__(self):
        self.to_restore = []
        self.focus = {}

    def save(self):
        self.to_restore = self.save_views()
        self.focus = self.save_active_focus()
        sublime.status_message("Saved layout of %i file(s)" % len(self.to_restore))

    # Attempt to restore the active window's groups to show the views they contained
    # when the user last activated the save_layout command.
    def restore(self):
        self.restore_views(self.to_restore)
        self.restore_active_focus(self.focus)
        sublime.status_message("Restored layout of %i file(s)." % len(self.to_restore))

    # When a view closes, store its filename so we can still restore something
    def closed(self, closed_view):
        for i, view in enumerate(self.to_restore):
            print "Checking %i against closing view %i" % (view.id(), closed_view.id())
            if view.id() == closed_view.id():
                self.to_restore[i] = closed_view.file_name()

    # Methods below this point in the class should be considered private.
    def save_views(self):
        panes = sublime.active_window().num_groups()
        views = []
        for i in range(panes):
            view = sublime.active_window().active_view_in_group(i)
            print "Noticed that group %i has view %s" % (i, (view.file_name() if view is not None and view.file_name() else view))
            views.append(view)
        return views

    def restore_views(self, views):
        window = sublime.active_window()
        for group_pos in range(len(views)):
            print "Will attempt to restore group %i with %s" % (group_pos, views[group_pos])
            if group_pos < window.num_groups() and views[group_pos] is not None:
                if isinstance(views[group_pos], unicode):
                    window.focus_group(group_pos)
                    views[group_pos] = window.open_file(views[group_pos]) # we store a filename when we detect a view closes
                elif views[group_pos] is not None:
                    window.set_view_index(views[group_pos], group_pos, 0)
                    window.focus_view(views[group_pos]) # Bring it to the front within its group        

    def save_active_focus(self):
        window = sublime.active_window()
        active = {}
        active['group'] = window.active_group()
        active['selection'] = []
        for region in window.active_view().sel():
            active['selection'].append(region)
        print "Saved active state: %s" % active
        return active

    def restore_active_focus(self, active):
        window = sublime.active_window()
        view = None
        if active['group'] is not None:
            window.focus_group(active['group'])
            view = window.active_view_in_group(active['group'])
            window.focus_view(view)
        if active['selection'] is not None and view is not None:
            print "restoring selection: %s" % active['selection']
            window.active_view().sel().clear()
            for region in active['selection']:
                window.active_view().sel().add(region)

layout_manager = SublimeLayoutManager()

class SublimeLayoutCloseDetection(sublime_plugin.EventListener):
    def on_close(self, view):
        layout_manager.closed(view)

class SaveLayoutCommand(sublime_plugin.WindowCommand):
    def run(self):
        layout_manager.save()

class RestoreLayoutCommand(sublime_plugin.WindowCommand):
    def run(self):
        layout_manager.restore()
