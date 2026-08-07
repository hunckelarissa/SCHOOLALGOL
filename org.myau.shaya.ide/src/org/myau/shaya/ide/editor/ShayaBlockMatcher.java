package org.myau.shaya.ide.editor;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

import org.eclipse.jface.text.BadLocationException;
import org.eclipse.jface.text.IDocument;

/**
 * Match ALG block keywords: нач/если/нц… ↔ кон/все/кц…
 * Skips comments/strings via {@link ShayaLexicalMask} (dialect comment style).
 */
public final class ShayaBlockMatcher {

	private static final Set<String> OPENERS = new HashSet<>();
	private static final Set<String> CLOSERS = new HashSet<>();

	static {
		for (String s : new String[] {
				"алг", "нач", "начало", "если", "пока", "для", "нц", "проц", "функ",
				"попытка", "попробуй", "цикл", "выбор", "модуль", "пока_не", "повторить"
		}) {
			OPENERS.add(s);
		}
		for (String s : new String[] {
				"кон", "все", "кц", "кесли", "кпока", "кдля", "кпр", "кфун",
				"кпопытка", "кон_цикл", "конец_выбора", "конмод", "кц_пока"
		}) {
			CLOSERS.add(s);
		}
	}

	private ShayaBlockMatcher() {
	}

	public static int findMatch(IDocument doc, int offset) throws BadLocationException {
		return findMatch(doc, offset, ShayaCommentStyle.LINE_SLASH);
	}

	public static int findMatch(IDocument doc, int offset, ShayaCommentStyle style)
			throws BadLocationException {
		if (doc == null) {
			return -1;
		}
		String text = doc.get();
		boolean[] mask = ShayaLexicalMask.mask(text, style);
		Token here = tokenAt(text, mask, offset);
		if (here == null) {
			return -1;
		}
		String w = here.word.toLowerCase(Locale.ROOT);
		if (OPENERS.contains(w)) {
			return findClosing(text, mask, here.end, w);
		}
		if (CLOSERS.contains(w)) {
			return findOpening(text, mask, here.start, w);
		}
		return -1;
	}

	/**
	 * Innermost (or next outer) block containing {@code offset}…{@code offset+selLen}.
	 * Returns {@code [start, length]} or {@code null}.
	 */
	public static int[] findEnclosing(IDocument doc, int offset, int selLen) throws BadLocationException {
		return findEnclosing(doc, offset, selLen, ShayaCommentStyle.LINE_SLASH);
	}

	public static int[] findEnclosing(IDocument doc, int offset, int selLen, ShayaCommentStyle style)
			throws BadLocationException {
		if (doc == null || offset < 0) {
			return null;
		}
		String text = doc.get();
		boolean[] mask = ShayaLexicalMask.mask(text, style);
		int selEnd = offset + Math.max(0, selLen);
		if (selLen == 0) {
			Token here = tokenAt(text, mask, offset);
			if (here != null) {
				int match = findMatch(doc, offset, style);
				if (match >= 0) {
					int a = Math.min(here.start, match);
					int bEnd = Math.max(here.end, match + keywordLength(text, mask, match));
					return new int[] { a, bEnd - a };
				}
			}
		}
		int i = Math.min(offset + 1, text.length());
		while (i > 0) {
			Token t = prevToken(text, mask, i);
			if (t == null) {
				break;
			}
			String w = t.word.toLowerCase(Locale.ROOT);
			if (OPENERS.contains(w)) {
				int close = findClosing(text, mask, t.end, w);
				if (close >= 0) {
					int closeEnd = close + keywordLength(text, mask, close);
					if (t.start <= offset && closeEnd >= selEnd) {
						if (!(selLen > 0 && t.start == offset && closeEnd == selEnd)) {
							return new int[] { t.start, closeEnd - t.start };
						}
					}
				}
			}
			i = t.start;
		}
		return null;
	}

	private static int keywordLength(String text, boolean[] mask, int start) {
		Token t = tokenAt(text, mask, start);
		return t != null ? (t.end - t.start) : 1;
	}

	private static int findClosing(String text, boolean[] mask, int from, String rootOpener) {
		Deque<String> stack = new ArrayDeque<>();
		stack.push(rootOpener);
		int i = from;
		while (i < text.length()) {
			Token t = nextToken(text, mask, i);
			if (t == null) {
				break;
			}
			String w = t.word.toLowerCase(Locale.ROOT);
			if (OPENERS.contains(w)) {
				stack.push(w);
			} else if (CLOSERS.contains(w)) {
				int matchIdx = indexOfMatchingOpener(stack, w);
				if (matchIdx >= 0) {
					while (stack.size() - 1 > matchIdx) {
						stack.removeLast();
					}
					stack.removeLast();
					if (stack.isEmpty()) {
						return t.start;
					}
				}
			}
			i = t.end;
		}
		return -1;
	}

	private static int findOpening(String text, boolean[] mask, int before, String rootCloser) {
		Deque<String> stack = new ArrayDeque<>();
		stack.push(rootCloser);
		int i = before;
		while (i > 0) {
			Token t = prevToken(text, mask, i);
			if (t == null) {
				break;
			}
			String w = t.word.toLowerCase(Locale.ROOT);
			if (CLOSERS.contains(w)) {
				stack.push(w);
			} else if (OPENERS.contains(w)) {
				// Match this opener against top closer if possible; else scan stack
				int matchIdx = indexOfMatchingCloser(stack, w);
				if (matchIdx >= 0) {
					while (stack.size() - 1 > matchIdx) {
						stack.removeLast();
					}
					stack.removeLast();
					if (stack.isEmpty()) {
						return t.start;
					}
				}
			}
			i = t.start;
		}
		return -1;
	}

	/** Index in deque (0 = bottom) of opener that {@code closer} may close; -1 if none. */
	private static int indexOfMatchingOpener(Deque<String> stack, String closer) {
		int idx = stack.size() - 1;
		for (String opener : reverseView(stack)) {
			if (ShayaBlockFamilies.closes(opener, closer)) {
				return idx;
			}
			idx--;
		}
		return -1;
	}

	/** Index of closer that may be closed by {@code opener} when scanning backward. */
	private static int indexOfMatchingCloser(Deque<String> stack, String opener) {
		int idx = stack.size() - 1;
		for (String closer : reverseView(stack)) {
			if (ShayaBlockFamilies.closes(opener, closer)) {
				return idx;
			}
			idx--;
		}
		return -1;
	}

	private static Iterable<String> reverseView(Deque<String> stack) {
		List<String> list = new ArrayList<>(stack);
		java.util.Collections.reverse(list);
		return list;
	}

	private static Token tokenAt(String text, boolean[] mask, int offset) {
		int start = offset;
		int len = text.length();
		if (start >= len) {
			start = len - 1;
		}
		if (start < 0) {
			return null;
		}
		if (ShayaLexicalMask.covered(mask, start)) {
			return null;
		}
		if (!isIdent(text.charAt(start)) && start > 0 && isIdent(text.charAt(start - 1))
				&& !ShayaLexicalMask.covered(mask, start - 1)) {
			start--;
		}
		while (start > 0 && isIdent(text.charAt(start - 1)) && !ShayaLexicalMask.covered(mask, start - 1)) {
			start--;
		}
		if (ShayaLexicalMask.covered(mask, start) || !isIdentStart(text.charAt(start))) {
			return null;
		}
		int end = start;
		while (end < len && isIdent(text.charAt(end)) && !ShayaLexicalMask.covered(mask, end)) {
			end++;
		}
		if (end <= start) {
			return null;
		}
		return new Token(text.substring(start, end), start, end);
	}

	private static Token nextToken(String text, boolean[] mask, int from) {
		int i = Math.max(0, from);
		int len = text.length();
		while (i < len) {
			if (ShayaLexicalMask.covered(mask, i)) {
				i++;
				continue;
			}
			char c = text.charAt(i);
			if (isIdentStart(c)) {
				int start = i++;
				while (i < len && isIdent(text.charAt(i)) && !ShayaLexicalMask.covered(mask, i)) {
					i++;
				}
				return new Token(text.substring(start, i), start, i);
			}
			i++;
		}
		return null;
	}

	private static Token prevToken(String text, boolean[] mask, int before) {
		int i = before - 1;
		while (i >= 0) {
			if (ShayaLexicalMask.covered(mask, i)) {
				i--;
				continue;
			}
			char c = text.charAt(i);
			if (isIdent(c)) {
				int end = i + 1;
				while (i > 0 && isIdent(text.charAt(i - 1)) && !ShayaLexicalMask.covered(mask, i - 1)) {
					i--;
				}
				if (isIdentStart(text.charAt(i)) && !ShayaLexicalMask.covered(mask, i)) {
					return new Token(text.substring(i, end), i, end);
				}
			}
			i--;
		}
		return null;
	}

	private static boolean isIdentStart(char c) {
		return Character.isLetter(c) || c == '_';
	}

	private static boolean isIdent(char c) {
		return Character.isLetterOrDigit(c) || c == '_';
	}

	private static final class Token {
		final String word;
		final int start;
		final int end;

		Token(String word, int start, int end) {
			this.word = word;
			this.start = start;
			this.end = end;
		}
	}
}
