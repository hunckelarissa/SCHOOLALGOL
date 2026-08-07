package org.myau.shaya.ide.editor;

/**
 * Insertable skeletons for Ctrl+Space — SCHOOLALGOL (.alg) dialect (RU + EN).
 * Cursor marked with {@code §}.
 */
public final class ShayaTemplates {

	private static final char CURSOR = '§';

	public static final class Template {
		public final String label;
		public final String body;
		public final int cursor;

		public Template(String label, String body, int cursor) {
			this.label = label;
			this.body = body;
			this.cursor = cursor;
		}
	}

	private ShayaTemplates() {
	}

	public static Template[] forDialect(ShayaKeywords.Dialect dialect) {
		return alg();
	}

	private static Template[] alg() {
		return new Template[] {
				// RU
				tpl("алг…", "алг основнаяпрограмма\nнач\n  §\nкон\n"),
				tpl("если…", "если § то\n  \nвсе\n"),
				tpl("если-иначе…", "если § то\n  \nиначе\n  \nвсе\n"),
				tpl("нц-пока…", "нц пока §\n  \nкц\n"),
				tpl("нц-для…", "нц для i от 1 до 10\n  §\nкц\n"),
				tpl("вывод…", "вывод \"§\"\n"),
				// EN
				tpl("proc…", "proc mainprogram\nbegin\n  §\nend\n"),
				tpl("if…", "if § then\n  \nendif\n"),
				tpl("if-else…", "if § then\n  \nelse\n  \nendif\n"),
				tpl("loop-while…", "loop while §\n  \neloop\n"),
				tpl("loop-for…", "loop for i from 1 to 10\n  §\neloop\n"),
				tpl("output…", "output \"§\"\n")
		};
	}

	private static Template tpl(String label, String raw) {
		int c = raw.indexOf(CURSOR);
		String body = raw.replace(String.valueOf(CURSOR), "");
		if (c < 0) {
			c = body.length();
		}
		return new Template(label, body, Math.min(c, body.length()));
	}
}
