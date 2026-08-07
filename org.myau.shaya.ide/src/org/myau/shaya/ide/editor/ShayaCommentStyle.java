package org.myau.shaya.ide.editor;

/** Comment style for Toggle Comment — SCHOOLALGOL uses {@code |} line comments. */
public enum ShayaCommentStyle {
	/** // line comments */
	LINE_SLASH,
	/** | line comments (classic Kushnirenko textbooks) */
	LINE_PIPE,
	/** (* … *) block comments */
	BLOCK_PAREN;

	public static ShayaCommentStyle forDialect(ShayaKeywords.Dialect dialect) {
		return LINE_PIPE;
	}
}
