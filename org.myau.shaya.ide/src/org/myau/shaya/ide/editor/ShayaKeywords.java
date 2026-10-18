package org.myau.shaya.ide.editor;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

import org.myau.shaya.ide.toolchain.ShayaToolchain;

/**
 * Kushnirenko / SCHOOLALGOL (.alg) keywords for syntax highlighting and completion.
 * Dialect is derived only from the file extension (same law as
 * {@link ShayaToolchain#engineIdFor(java.io.File)}).
 */
public final class ShayaKeywords {

	private ShayaKeywords() {
	}

	public enum Dialect {
		/** Classic Kushnirenko SCHOOLALGOL (.alg). */
		ALG,
		GENERIC
	}

	/** .alg — Kushnirenko + EN aliases (proc/begin/end, if/then/endif, loop/eloop, …). */
	public static final String[] ALG = {
			"алг", "арг", "нач", "кон", "конст", "ввод", "вывод", "если", "то", "иначе", "все",
			"нц", "пока", "для", "от", "до", "кц", "рез", "использовать", "выход", "продолжить", "возврат", "шаг",
			"proc", "arg", "res", "begin", "end", "const", "input", "output",
			"if", "then", "else", "endif", "loop", "eloop", "for", "while", "from", "to", "import", "break", "continue", "return", "step"
	};
	public static final String[] ALG_TYPES = {
			"цел", "вещ", "лог", "лит", "таб", "файл", "запись", "переч", "словарь",
			"int", "real", "bool", "str", "tab", "file", "rec", "enum", "dict"
	};
	public static final String[] ALG_LITERALS = {
			"да", "нет", "и", "или", "не", "true", "false", "and", "or", "not"
	};
	/** Встроенные функции/процедуры (подсветка BUILTIN). */
	public static final String[] ALG_BUILTINS = {
			"открыть", "закрыть", "конецфайла", "корень", "модуль", "случ", "случцел",
			"длина", "подстрока", "вверх", "вниз", "вцел", "ввещ", "встроку",
			"остаток", "целдел", "степень", "мин", "макс", "округление", "знак",
			"sin", "cos", "син", "кос", "найти", "размер",
			"open", "close", "eof", "sqrt", "abs", "rand", "randint",
			"len", "substr", "upper", "lower", "toint", "toreal", "tostr",
			"mod", "div", "pow", "min", "max", "round", "sign", "find", "size"
	};

	public static Dialect dialectOfFileName(String name) {
		String engine = ShayaToolchain.engineIdForName(name);
		if (ShayaToolchain.ENGINE_ALG.equals(engine)) {
			return Dialect.ALG;
		}
		return Dialect.GENERIC;
	}

	/** Control keywords for the given dialect (highlighter). */
	public static String[] controlFor(Dialect dialect) {
		return ALG;
	}

	/** Type keywords for the given dialect (highlighter). */
	public static String[] typesFor(Dialect dialect) {
		return ALG_TYPES;
	}

	/** Literals + built-in functions for the given dialect (highlighter). */
	public static String[] builtinsFor(Dialect dialect) {
		String[] out = new String[ALG_LITERALS.length + ALG_BUILTINS.length];
		System.arraycopy(ALG_LITERALS, 0, out, 0, ALG_LITERALS.length);
		System.arraycopy(ALG_BUILTINS, 0, out, ALG_LITERALS.length, ALG_BUILTINS.length);
		return out;
	}

	/** All proposals (control + types + builtins), unique + sorted, for the given dialect. */
	public static String[] proposalsFor(Dialect dialect) {
		List<String[]> groups = new ArrayList<>();
		groups.add(controlFor(dialect));
		groups.add(typesFor(dialect));
		groups.add(builtinsFor(dialect));
		int n = 0;
		for (String[] g : groups) {
			n += g.length;
		}
		String[] all = new String[n];
		int i = 0;
		for (String[] g : groups) {
			System.arraycopy(g, 0, all, i, g.length);
			i += g.length;
		}
		return uniqueSorted(all);
	}

	public static boolean isKeyword(String word, Dialect dialect) {
		if (word == null || word.isEmpty()) {
			return false;
		}
		String lower = word.toLowerCase(Locale.ROOT);
		return containsIgnoreCase(controlFor(dialect), lower) || containsIgnoreCase(typesFor(dialect), lower)
				|| containsIgnoreCase(builtinsFor(dialect), lower);
	}

	private static boolean containsIgnoreCase(String[] words, String lower) {
		for (String w : words) {
			if (w != null && w.toLowerCase(Locale.ROOT).equals(lower)) {
				return true;
			}
		}
		return false;
	}

	private static String[] uniqueSorted(String[] raw) {
		Set<String> set = new LinkedHashSet<>();
		for (String s : raw) {
			if (s != null && !s.isEmpty()) {
				set.add(s);
			}
		}
		String[] arr = set.toArray(new String[0]);
		Arrays.sort(arr, Comparator.naturalOrder());
		return arr;
	}
}
