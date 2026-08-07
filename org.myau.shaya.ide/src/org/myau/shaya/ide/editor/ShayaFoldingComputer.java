package org.myau.shaya.ide.editor;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Stack;

import org.eclipse.jface.text.BadLocationException;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.Position;

/**
 * Fold ALG blocks on matching opener/closer families (не любой кон на любой если).
 * Skips comment/string lines via {@link ShayaLexicalMask}.
 */
public final class ShayaFoldingComputer {

	private static final class Frame {
		final int offset;
		final String opener;

		Frame(int offset, String opener) {
			this.offset = offset;
			this.opener = opener;
		}
	}

	private ShayaFoldingComputer() {
	}

	public static List<Position> computeFoldingPositions(IDocument document) {
		return computeFoldingPositions(document, ShayaCommentStyle.LINE_SLASH);
	}

	public static List<Position> computeFoldingPositions(IDocument document, ShayaCommentStyle style) {
		List<Position> result = new ArrayList<>();
		if (document == null) {
			return result;
		}
		String text;
		try {
			text = document.get();
		} catch (Exception e) {
			return result;
		}
		boolean[] mask = ShayaLexicalMask.mask(text, style != null ? style : ShayaCommentStyle.LINE_SLASH);
		Stack<Frame> starts = new Stack<>();
		int lines = document.getNumberOfLines();
		try {
			for (int line = 0; line < lines; line++) {
				String word = firstCodeWord(document, mask, line);
				if (word == null) {
					continue;
				}
				String lower = word.toLowerCase(Locale.ROOT);
				if (ShayaIndent.isOpener(lower) && ShayaBlockFamilies.openerFamily(lower) != null) {
					starts.push(new Frame(document.getLineOffset(line), lower));
				} else if (ShayaIndent.isCloser(lower)) {
					int matchIdx = -1;
					for (int i = starts.size() - 1; i >= 0; i--) {
						if (ShayaBlockFamilies.closes(starts.get(i).opener, lower)) {
							matchIdx = i;
							break;
						}
					}
					if (matchIdx < 0) {
						continue;
					}
					while (starts.size() - 1 > matchIdx) {
						starts.pop();
					}
					Frame frame = starts.pop();
					int startLine = document.getLineOfOffset(frame.offset);
					if (line > startLine) {
						int end = document.getLineOffset(line) + document.getLineLength(line);
						result.add(new Position(frame.offset, end - frame.offset));
					}
				}
			}
		} catch (BadLocationException ignored) {
		}
		return result;
	}

	private static String firstCodeWord(IDocument document, boolean[] mask, int line)
			throws BadLocationException {
		int offset = document.getLineOffset(line);
		int length = document.getLineLength(line);
		int end = offset + length;
		int i = offset;
		while (i < end && i < mask.length) {
			char c = document.getChar(i);
			if (c == '\r' || c == '\n') {
				break;
			}
			if (Character.isWhitespace(c)) {
				i++;
				continue;
			}
			if (ShayaLexicalMask.covered(mask, i)) {
				return null;
			}
			if (!Character.isLetter(c) && c != '_') {
				return null;
			}
			int start = i++;
			while (i < end && i < mask.length && !ShayaLexicalMask.covered(mask, i)
					&& (Character.isLetterOrDigit(document.getChar(i)) || document.getChar(i) == '_')) {
				i++;
			}
			return document.get(start, i - start);
		}
		return null;
	}
}
