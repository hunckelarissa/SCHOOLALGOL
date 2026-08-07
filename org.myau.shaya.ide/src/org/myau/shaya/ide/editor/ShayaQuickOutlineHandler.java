package org.myau.shaya.ide.editor;

import java.util.List;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.viewers.LabelProvider;
import org.eclipse.jface.window.Window;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.dialogs.ElementListSelectionDialog;
import org.eclipse.ui.handlers.HandlerUtil;
import org.myau.shaya.ide.outline.ShayaContentOutlinePage;

/** Quick Outline (Ctrl+O) — jump to алг / проц / функ / модуль / нач. */
public class ShayaQuickOutlineHandler extends AbstractHandler {

	@Override
	public Object execute(ExecutionEvent event) throws ExecutionException {
		IEditorPart part = HandlerUtil.getActiveEditor(event);
		if (!(part instanceof ShayaEditor)) {
			return null;
		}
		ShayaEditor editor = (ShayaEditor) part;
		IDocument doc = editor.getEditorDocument();
		Shell shell = HandlerUtil.getActiveShell(event);
		if (doc == null || shell == null) {
			return null;
		}
		List<ShayaContentOutlinePage.OutlineItem> hits = ShayaContentOutlinePage.listSymbols(doc,
				ShayaCommentStyle.forDialect(editor.currentDialect()));
		if (hits.isEmpty()) {
			MessageDialog.openInformation(shell, "Quick Outline",
					"No алг / проц / функ / модуль / нач found.");
			return null;
		}
		ElementListSelectionDialog dlg = new ElementListSelectionDialog(shell, new LabelProvider());
		dlg.setTitle("Quick Outline");
		dlg.setMessage("Filter and select:");
		dlg.setElements(hits.toArray());
		if (dlg.open() != Window.OK
				|| !(dlg.getFirstResult() instanceof ShayaContentOutlinePage.OutlineItem)) {
			return null;
		}
		ShayaContentOutlinePage.OutlineItem item = (ShayaContentOutlinePage.OutlineItem) dlg
				.getFirstResult();
		editor.selectAndReveal(item.offset, item.length);
		return null;
	}
}
