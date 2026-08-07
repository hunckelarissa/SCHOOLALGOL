package org.myau.shaya.ide.editor;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.jface.text.BadLocationException;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.ITextSelection;
import org.eclipse.jface.text.TextSelection;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.handlers.HandlerUtil;

/**
 * Toggle comment using the dialect style of the current file extension
 * (// or | line, or (*…*) for Vetka_B). Never guesses dialect from text.
 */
public class ShayaToggleCommentHandler extends AbstractHandler {

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
		ITextSelection sel = null;
		if (editor.getSelectionProvider().getSelection() instanceof ITextSelection) {
			sel = (ITextSelection) editor.getSelectionProvider().getSelection();
		}
		if (sel == null) {
			return null;
		}
		ShayaCommentStyle style = ShayaCommentStyle.forDialect(editor.currentDialect());
		try {
			if (style == ShayaCommentStyle.BLOCK_PAREN) {
				toggleBlock(doc, editor, sel);
			} else {
				String prefix = style == ShayaCommentStyle.LINE_PIPE ? "| " : "// ";
				toggleLine(doc, editor, sel, prefix);
			}
		} catch (BadLocationException ignored) {
		}
		return null;
	}

	private static void toggleLine(IDocument doc, ShayaEditor editor, ITextSelection sel, String prefix)
			throws BadLocationException {
		int startLine = doc.getLineOfOffset(sel.getOffset());
		int endLine = doc.getLineOfOffset(sel.getOffset() + Math.max(0, sel.getLength()));
		boolean allCommented = true;
		for (int line = startLine; line <= endLine; line++) {
			String text = lineText(doc, line);
			String t = text.trim();
			if (t.isEmpty()) {
				continue;
			}
			if (!(t.startsWith(prefix.trim()) || t.startsWith(prefix))) {
				allCommented = false;
				break;
			}
		}
		for (int line = startLine; line <= endLine; line++) {
			int off = doc.getLineOffset(line);
			int len = doc.getLineLength(line);
			String raw = doc.get(off, len);
			String nl = "";
			String body = raw;
			if (body.endsWith("\r\n")) {
				nl = "\r\n";
				body = body.substring(0, body.length() - 2);
			} else if (body.endsWith("\n") || body.endsWith("\r")) {
				nl = body.substring(body.length() - 1);
				body = body.substring(0, body.length() - 1);
			}
			String trimmed = body.trim();
			if (trimmed.isEmpty()) {
				continue;
			}
			int lead = 0;
			while (lead < body.length() && Character.isWhitespace(body.charAt(lead))) {
				lead++;
			}
			String indent = body.substring(0, lead);
			String rest = body.substring(lead);
			String next;
			if (allCommented) {
				if (rest.startsWith(prefix)) {
					next = indent + rest.substring(prefix.length());
				} else if (rest.startsWith(prefix.trim())) {
					String p = prefix.trim();
					next = indent + rest.substring(p.length());
					if (next.startsWith(" ")) {
						next = next.substring(1);
					}
				} else {
					next = body;
				}
			} else {
				next = indent + prefix + rest;
			}
			doc.replace(off, len, next + nl);
		}
		editor.getSelectionProvider().setSelection(new TextSelection(doc.getLineOffset(startLine), 0));
	}

	private static String lineText(IDocument doc, int line) throws BadLocationException {
		int off = doc.getLineOffset(line);
		int len = doc.getLineLength(line);
		return doc.get(off, len).replace("\r", "").replace("\n", "");
	}

	private static void toggleBlock(IDocument doc, ShayaEditor editor, ITextSelection sel)
			throws BadLocationException {
		int start = sel.getOffset();
		int length = sel.getLength();
		if (length == 0) {
			int line = doc.getLineOfOffset(start);
			start = doc.getLineOffset(line);
			length = doc.getLineLength(line);
			while (length > 0) {
				char c = doc.getChar(start + length - 1);
				if (c == '\n' || c == '\r') {
					length--;
				} else {
					break;
				}
			}
		}
		String text = doc.get(start, length);
		String trimmed = text.trim();
		if (trimmed.startsWith("(*") && trimmed.endsWith("*)") && trimmed.length() >= 4) {
			int lead = 0;
			while (lead < text.length() && Character.isWhitespace(text.charAt(lead))) {
				lead++;
			}
			int trail = 0;
			while (trail < text.length() - lead
					&& Character.isWhitespace(text.charAt(text.length() - 1 - trail))) {
				trail++;
			}
			String inner = text.substring(lead + 2, text.length() - trail - 2);
			doc.replace(start, length, text.substring(0, lead) + inner + text.substring(text.length() - trail));
			editor.getSelectionProvider().setSelection(new TextSelection(start + lead, inner.length()));
		} else {
			String wrapped = "(*" + text + "*)";
			doc.replace(start, length, wrapped);
			editor.getSelectionProvider().setSelection(new TextSelection(start, wrapped.length()));
		}
	}
}
