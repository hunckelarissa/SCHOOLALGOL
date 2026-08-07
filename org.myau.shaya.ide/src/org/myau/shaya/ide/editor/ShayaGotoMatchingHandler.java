package org.myau.shaya.ide.editor;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.ITextSelection;
import org.eclipse.jface.text.TextSelection;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.handlers.HandlerUtil;

/** Jump between нач/если/нц… and matching кон/все/кц…. */
public class ShayaGotoMatchingHandler extends AbstractHandler {

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
		int offset = -1;
		if (editor.getSelectionProvider().getSelection() instanceof ITextSelection) {
			offset = ((ITextSelection) editor.getSelectionProvider().getSelection()).getOffset();
		}
		if (offset < 0) {
			return null;
		}
		try {
			ShayaCommentStyle style = ShayaCommentStyle.forDialect(editor.currentDialect());
			int match = ShayaBlockMatcher.findMatch(doc, offset, style);
			if (match >= 0) {
				int len = 1;
				while (match + len < doc.getLength()
						&& (Character.isLetterOrDigit(doc.getChar(match + len))
								|| doc.getChar(match + len) == '_')) {
					len++;
				}
				editor.getSelectionProvider().setSelection(new TextSelection(match, len));
				editor.getSourceViewerPublic().revealRange(match, len);
			}
		} catch (Exception ignored) {
		}
		return null;
	}
}
