package org.myau.shaya.ide.editor;

import org.myau.shaya.ide.Activator;
import org.myau.shaya.ide.prefs.ShayaPreferenceConstants;

import java.util.Locale;

import org.eclipse.jface.preference.IPreferenceStore;

/** Shared indent helpers for Reindent and Enter auto-indent. */
public final class ShayaIndent {

	private ShayaIndent() {
	}

	/** Current indent unit from Preferences (spaces or one tab). */
	public static String unit() {
		IPreferenceStore prefs = store();
		if (prefs != null && !prefs.getBoolean(ShayaPreferenceConstants.INSERT_SPACES)) {
			return "\t";
		}
		return repeat(" ", width());
	}

	/** Display / tab width (spaces per indent level). */
	public static int width() {
		IPreferenceStore prefs = store();
		int w = prefs != null ? prefs.getInt(ShayaPreferenceConstants.INDENT_WIDTH) : 2;
		if (w != 4 && w != 2) {
			return w < 3 ? 2 : 4;
		}
		return w;
	}

	private static IPreferenceStore store() {
		try {
			return Activator.getDefault() != null ? Activator.getDefault().getPreferenceStore() : null;
		} catch (Exception e) {
			return null;
		}
	}

	public static boolean isComment(String trimmed) {
		return trimmed.startsWith("//") || trimmed.startsWith("|") || trimmed.startsWith("(*");
	}

	public static String leadingKeyword(String trimmed) {
		int i = 0;
		while (i < trimmed.length() && ShayaIdentifiers.isIdentPart(trimmed.charAt(i))) {
			i++;
		}
		return trimmed.substring(0, i).toLowerCase(Locale.ROOT);
	}

	public static boolean isCloserOrMid(String kw) {
		return isCloser(kw) || "иначе".equals(kw) || "инес".equals(kw) || "иначе_если".equals(kw);
	}

	public static boolean isCloser(String kw) {
		return "кон".equals(kw) || "все".equals(kw) || "кц".equals(kw) || "кесли".equals(kw)
				|| "кпока".equals(kw) || "кдля".equals(kw) || "кпр".equals(kw) || "кфун".equals(kw)
				|| "кпопытка".equals(kw) || "кон_цикл".equals(kw) || "конец_выбора".equals(kw)
				|| "конмод".equals(kw) || "кц_пока".equals(kw);
	}

	public static boolean isOpener(String kw) {
		return "алг".equals(kw) || "нач".equals(kw) || "начало".equals(kw) || "если".equals(kw)
				|| "пока".equals(kw) || "для".equals(kw) || "нц".equals(kw) || "проц".equals(kw)
				|| "функ".equals(kw) || "попытка".equals(kw) || "попробуй".equals(kw) || "цикл".equals(kw)
				|| "выбор".equals(kw) || "модуль".equals(kw) || "пока_не".equals(kw) || "повторить".equals(kw);
	}

	/** True if previous line opens a block that should deepen the next line. */
	public static boolean opensBlock(String trimmed) {
		if (trimmed == null || trimmed.isEmpty() || isComment(trimmed)) {
			return false;
		}
		String kw = leadingKeyword(trimmed);
		if (!isOpener(kw)) {
			return false;
		}
		String lower = trimmed.toLowerCase(Locale.ROOT);
		return !(containsKeyword(lower, "кон") || containsKeyword(lower, "все")
				|| containsKeyword(lower, "кц") || containsKeyword(lower, "кесли"));
	}

	public static String leadingWhitespace(String line) {
		int i = 0;
		while (i < line.length()) {
			char c = line.charAt(i);
			if (c != ' ' && c != '\t') {
				break;
			}
			i++;
		}
		return line.substring(0, i);
	}

	public static String repeat(String s, int n) {
		if (n <= 0) {
			return "";
		}
		StringBuilder sb = new StringBuilder(s.length() * n);
		for (int i = 0; i < n; i++) {
			sb.append(s);
		}
		return sb.toString();
	}

	private static boolean containsKeyword(String lower, String kw) {
		int idx = lower.indexOf(kw);
		while (idx >= 0) {
			boolean leftOk = idx == 0 || !ShayaIdentifiers.isIdentPart(lower.charAt(idx - 1));
			int end = idx + kw.length();
			boolean rightOk = end >= lower.length() || !ShayaIdentifiers.isIdentPart(lower.charAt(end));
			if (leftOk && rightOk) {
				return true;
			}
			idx = lower.indexOf(kw, idx + 1);
		}
		return false;
	}
}
