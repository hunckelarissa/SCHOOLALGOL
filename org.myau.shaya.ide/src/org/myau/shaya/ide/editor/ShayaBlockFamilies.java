package org.myau.shaya.ide.editor;

/**
 * Opener/closer families for folding and block match — avoid {@code кон} closing {@code если}.
 */
public final class ShayaBlockFamilies {

	private ShayaBlockFamilies() {
	}

	/** Family id for an opener keyword, or null if not an opener. */
	public static String openerFamily(String kw) {
		if (kw == null) {
			return null;
		}
		switch (kw) {
		case "алг":
		case "нач":
		case "начало":
		case "проц":
		case "функ":
		case "модуль":
			return "body";
		case "если":
			return "if";
		case "пока":
		case "для":
		case "нц":
		case "цикл":
		case "пока_не":
		case "повторить":
			return "loop";
		case "попытка":
		case "попробуй":
			return "try";
		case "выбор":
			return "choice";
		default:
			return null;
		}
	}

	/** True if {@code closer} may close a block opened by {@code opener}. */
	public static boolean closes(String opener, String closer) {
		String fam = openerFamily(opener);
		if (fam == null || closer == null) {
			return false;
		}
		switch (closer) {
		case "кон":
		case "конмод":
			return "body".equals(fam);
		case "кпр":
		case "кфун":
			return "body".equals(fam);
		case "кесли":
			return "if".equals(fam);
		case "все":
			return "if".equals(fam) || "choice".equals(fam);
		case "конец_выбора":
			return "choice".equals(fam);
		case "кц":
		case "кпока":
		case "кдля":
		case "кон_цикл":
		case "кц_пока":
			return "loop".equals(fam);
		case "кпопытка":
			return "try".equals(fam);
		default:
			return false;
		}
	}
}
