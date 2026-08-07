package org.myau.shaya.ide.editor;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.ITextSelection;
import org.eclipse.jface.text.TextSelection;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.handlers.HandlerUtil;

/** Expand selection to the enclosing нач…кон / если…все / нц…кц block. */
public class ShayaExpandSelectionHandler extends AbstractHandler {

	@Override
	public Object execute(ExecutionEvent event) throws ExecutionException {
		IEditorPart part = HandlerUtil.getActiveEditor(event);
		if (!(part instanceof ShayaEditor)) {
			return null;
		}
		ShayaEditor editor = (ShayaEditor) part;
		IDocument doc = editor.getEditorDocument();
		if (doc == null) {
			return null;
		}
		int offset = 0;
		int length = 0;
		if (editor.getSelectionProvider().getSelection() instanceof ITextSelection) {
			ITextSelection sel = (ITextSelection) editor.getSelectionProvider().getSelection();
			offset = sel.getOffset();
			length = sel.getLength();
		}
		try {
			ShayaCommentStyle style = ShayaCommentStyle.forDialect(editor.currentDialect());
			int[] range = ShayaBlockMatcher.findEnclosing(doc, offset, length, style);
			if (range != null) {
				editor.getSelectionProvider().setSelection(new TextSelection(range[0], range[1]));
				editor.getSourceViewerPublic().revealRange(range[0], range[1]);
			}
		} catch (Exception ignored) {
		}
		return null;
	}
}
