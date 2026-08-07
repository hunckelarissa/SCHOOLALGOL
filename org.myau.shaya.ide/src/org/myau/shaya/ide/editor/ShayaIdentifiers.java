package org.myau.shaya.ide.editor;

import org.eclipse.jface.text.BadLocationException;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.ITextSelection;
import org.eclipse.jface.text.TextSelection;

/** Shared identifier helpers for Find Refs / Rename / hover. */
public final class ShayaIdentifiers {

	private ShayaIdentifiers() {
	}

	public static String wordAt(ShayaEditor editor, IDocument doc) {
		try {
			int offset = 0;
			if (editor.getSelectionProvider().getSelection() instanceof ITextSelection) {
				ITextSelection sel = (ITextSelection) editor.getSelectionProvider().getSelection();
				if (sel.getLength() > 0) {
					return doc.get(sel.getOffset(), sel.getLength()).trim();
				}
				offset = sel.getOffset();
			}
			return wordAtOffset(doc, offset);
		} catch (BadLocationException e) {
			return null;
		}
	}

	public static String wordAtOffset(IDocument doc, int offset) throws BadLocationException {
		int start = offset;
		while (start > 0 && isIdentPart(doc.getChar(start - 1))) {
			start--;
		}
		int end = offset;
		while (end < doc.getLength() && isIdentPart(doc.getChar(end))) {
			end++;
		}
		if (end <= start) {
			return null;
		}
		return doc.get(start, end - start);
	}

	public static boolean isIdentStart(char c) {
		return Character.isLetter(c) || c == '_';
	}

	public static boolean isIdentPart(char c) {
		return Character.isLetterOrDigit(c) || c == '_';
	}

	public static boolean isIdentName(String t) {
		if (t == null || t.isEmpty()) {
			return false;
		}
		if (!isIdentStart(t.charAt(0))) {
			return false;
		}
		for (int i = 1; i < t.length(); i++) {
			if (!isIdentPart(t.charAt(i))) {
				return false;
			}
		}
		return true;
	}

	public static ITextSelection emptySelection() {
		return new TextSelection(0, 0);
	}
}
