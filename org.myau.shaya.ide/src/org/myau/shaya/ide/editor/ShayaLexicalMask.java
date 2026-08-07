package org.myau.shaya.ide.editor;

/**
 * Marks comment / string regions so Rename, Find Refs, and occurrence
 * highlighting ignore dialect-shaped noise (extension → dialect law).
 */
public final class ShayaLexicalMask {

	private ShayaLexicalMask() {
	}

	/** {@code true} at each offset that lies inside a comment or string. */
	public static boolean[] mask(String text, ShayaCommentStyle style) {
		boolean[] m = new boolean[text == null ? 0 : text.length()];
		if (text == null || text.isEmpty()) {
			return m;
		}
		if (style == null) {
			style = ShayaCommentStyle.LINE_SLASH;
		}
		int i = 0;
		while (i < text.length()) {
			char c = text.charAt(i);
			if (c == '"' || c == '\'') {
				i = markQuoted(text, m, i);
				continue;
			}
			switch (style) {
			case LINE_PIPE:
				if (c == '|') {
					i = markLine(text, m, i);
					continue;
				}
				break;
			case BLOCK_PAREN:
				if (c == '(' && peek(text, i + 1, '*')) {
					i = markBlock(text, m, i, '*', ')');
					continue;
				}
				break;
			case LINE_SLASH:
			default:
				if (c == '/' && peek(text, i + 1, '/')) {
					i = markLine(text, m, i);
					continue;
				}
				if (c == '/' && peek(text, i + 1, '*')) {
					i = markBlock(text, m, i, '*', '/');
					continue;
				}
				if (c == '#') {
					i = markLine(text, m, i);
					continue;
				}
				break;
			}
			i++;
		}
		return m;
	}

	public static boolean covered(boolean[] mask, int offset) {
		return mask != null && offset >= 0 && offset < mask.length && mask[offset];
	}

	private static boolean peek(String text, int i, char expected) {
		return i < text.length() && text.charAt(i) == expected;
	}

	private static int markQuoted(String text, boolean[] m, int i) {
		char q = text.charAt(i);
		m[i++] = true;
		while (i < text.length()) {
			m[i] = true;
			char c = text.charAt(i);
			if (c == '\\' && i + 1 < text.length()) {
				i++;
				m[i] = true;
				i++;
				continue;
			}
			i++;
			if (c == q) {
				break;
			}
		}
		return i;
	}

	private static int markLine(String text, boolean[] m, int i) {
		while (i < text.length()) {
			char c = text.charAt(i);
			if (c == '\n' || c == '\r') {
				break;
			}
			m[i++] = true;
		}
		return i;
	}

	/** Start at opening of {@code /*} or {@code (*}; closer is {@code *}/ or {@code *)}. */
	private static int markBlock(String text, boolean[] m, int i, char mid, char end) {
		m[i++] = true;
		if (i < text.length()) {
			m[i++] = true;
		}
		while (i < text.length()) {
			m[i] = true;
			if (text.charAt(i) == mid && peek(text, i + 1, end)) {
				i++;
				m[i] = true;
				i++;
				break;
			}
			i++;
		}
		return i;
	}
}
